#!/usr/bin/env python3
"""
Cobalt Repository Social Network Analysis

This script analyzes all user activity on the icebreakerlabs/cobalt repository 
using social network analysis to understand team collaboration patterns and engineering metrics.

Run this script to:
1. Discover all contributors to the repository
2. Collect GitHub activity data
3. Perform comprehensive social network analysis
4. Generate visualizations and insights
5. Export data to CSV files
"""

import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json
import os
import datetime
import subprocess
from typing import List, Dict, Any
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

def main():
    # Configuration
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    REPO_OWNER = 'icebreakerlabs'
    REPO_NAME = 'cobalt'
    
    # Analysis period (adjustable)
    DAYS_BACK = 30  # Change this to analyze different time periods
    since_date = (datetime.datetime.now() - datetime.timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')
    until_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    print(f"Analyzing activity from {since_date} to {until_date}")
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")
    
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set")
        return
    
    # Step 1: Discover All Contributors
    print("\n1. Discovering repository contributors...")
    contributors = get_repo_contributors(REPO_OWNER, REPO_NAME, GITHUB_TOKEN)
    print(f"Found {len(contributors)} contributors:")
    for contributor in contributors:
        print(f"  - {contributor}")
    
    # Step 2: Generate Repository Configuration
    print("\n2. Creating repository configuration...")
    config_path = create_repos_config(contributors, REPO_OWNER, REPO_NAME)
    print(f"Created configuration file: {config_path}")
    
    # Step 3: Collect GitHub Activity Data
    print("\n3. Collecting GitHub activity data...")
    data_file = collect_github_data(config_path, since_date, until_date, REPO_NAME)
    
    # Step 4: Load and Prepare Data
    print("\n4. Loading and preparing data...")
    if data_file:
        df = load_and_prepare_data(data_file)
    else:
        print("No data file available. Please check the data collection step.")
        return
    
    # Step 5: Build Social Network Graph
    print("\n5. Building social network graph...")
    G = build_social_network(df)
    
    # Step 6: Calculate Social Network Analysis Metrics
    print("\n6. Calculating SNA metrics...")
    sna_metrics = calculate_sna_metrics(G)
    
    # Step 7: Create Visualizations
    print("\n7. Creating visualizations...")
    create_network_visualizations(G, sna_metrics, df)
    
    # Step 8: Export Data
    print("\n8. Exporting data...")
    export_data(df, sna_metrics, G, contributors, REPO_OWNER, REPO_NAME, DAYS_BACK, since_date, until_date)
    
    # Step 9: Generate Insights
    print("\n9. Generating insights...")
    generate_insights(sna_metrics, G, df)
    
    print("\nAnalysis complete! Check the data/ directory for exported CSV files.")

def get_repo_contributors(owner: str, repo: str, token: str) -> List[str]:
    """Get all contributors to a repository"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}/contributors'
    contributors = []
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            contributors.extend([user['login'] for user in data])
            
            # Check for next page
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        else:
            print(f"Error fetching contributors: {response.status_code}")
            break
    
    return contributors

def create_repos_config(contributors: List[str], owner: str, repo: str) -> str:
    """Create repos.json configuration for all contributors"""
    config = []
    for contributor in contributors:
        config.append({
            "username": contributor,
            "owner": owner,
            "repo": repo
        })
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, f"data/cobalt_{repo}_repos.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def collect_github_data(config_path: str, since_date: str, until_date: str, repo_name: str) -> str:
    """Collect GitHub data using the existing tool"""
    output_file = f"data/cobalt_{repo_name}_activity.csv"
    
    # Get the project root directory (parent of notebooks/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    cmd = [
        "uv", "run", os.path.join(project_root, "main.py"), "collect",
        "--repos", os.path.join(project_root, config_path),
        "--output", "csv",
        "--output-file", os.path.join(project_root, output_file),
        "--since-iso", since_date,
        "--until-iso", until_date
    ]
    
    print("Collecting GitHub activity data...")
    print(f"Running command from: {project_root}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
    
    if result.returncode == 0:
        print(f"Data collected successfully: {output_file}")
        return output_file
    else:
        print(f"Error collecting data: {result.stderr}")
        return None

def load_and_prepare_data(file_path: str) -> pd.DataFrame:
    """Load and prepare the collected data"""
    # If file_path is relative, make it absolute from project root
    if not os.path.isabs(file_path):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(project_root, file_path)
    
    if not os.path.exists(file_path):
        print(f"Data file not found: {file_path}")
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    
    # Clean and prepare data
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df = df[df['created_at'].notnull()]
    df['title'] = df['title'].fillna('[No Title]')
    
    # Remove duplicates
    df.drop_duplicates(inplace=True)
    
    print(f"Loaded {len(df)} activity records")
    print(f"Date range: {df['created_at'].min()} to {df['created_at'].max()}")
    print(f"Unique users: {df['source'].nunique()}")
    print(f"Activity types: {df['type'].value_counts().to_dict()}")
    
    return df

def build_social_network(df: pd.DataFrame) -> nx.Graph:
    """Build a social network graph from activity data"""
    if df.empty:
        return nx.Graph()
    
    # Create graph from edges
    G = nx.from_pandas_edgelist(df, source='source', target='target', edge_attr=['type', 'created_at', 'title'])
    
    # Add node attributes
    for node in G.nodes():
        # Node activity metrics
        node_edges = list(G.edges(node, data=True))
        G.nodes[node]['activity_count'] = len(node_edges)
        G.nodes[node]['first_activity'] = min([edge[2]['created_at'] for edge in node_edges]) if node_edges else None
        G.nodes[node]['last_activity'] = max([edge[2]['created_at'] for edge in node_edges]) if node_edges else None
        
        # Activity type distribution
        activity_types = [edge[2]['type'] for edge in node_edges]
        G.nodes[node]['activity_types'] = dict(Counter(activity_types))
    
    print(f"Built network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def calculate_sna_metrics(G: nx.Graph) -> pd.DataFrame:
    """Calculate comprehensive social network analysis metrics"""
    if G.number_of_nodes() == 0:
        return pd.DataFrame()
    
    metrics = {}
    
    # Calculate centrality measures that work with disconnected graphs
    try:
        eigenvector_cent = nx.eigenvector_centrality_numpy(G)
    except nx.AmbiguousSolution:
        # For disconnected graphs, use a different approach
        eigenvector_cent = {}
        for node in G.nodes():
            # Calculate eigenvector centrality for each connected component
            component = nx.node_connected_component(G, node)
            if len(component) > 1:
                subgraph = G.subgraph(component)
                try:
                    sub_cent = nx.eigenvector_centrality_numpy(subgraph)
                    eigenvector_cent[node] = sub_cent.get(node, 0)
                except:
                    eigenvector_cent[node] = 0
            else:
                eigenvector_cent[node] = 0
    
    for node in G.nodes():
        # Eccentricity: handle disconnected graphs
        try:
            component = nx.node_connected_component(G, node)
            subgraph = G.subgraph(component)
            eccentricity = nx.eccentricity(subgraph, v=node)
        except Exception:
            eccentricity = 0
        metrics[node] = {
            # Basic metrics
            'degree': G.degree(node),
            'activity_count': G.nodes[node]['activity_count'],
            
            # Centrality measures
            'betweenness_centrality': nx.betweenness_centrality(G).get(node, 0),
            'closeness_centrality': nx.closeness_centrality(G).get(node, 0),
            'eigenvector_centrality': eigenvector_cent.get(node, 0),
            'pagerank': nx.pagerank(G).get(node, 0),
            
            # Clustering and connectivity
            'clustering_coefficient': nx.clustering(G, node),
            'local_efficiency': nx.local_efficiency(G) if G.number_of_nodes() > 1 else 0,
            
            # Network position
            'eccentricity': eccentricity,
            'average_neighbor_degree': nx.average_neighbor_degree(G).get(node, 0),
            
            # Activity timing
            'first_activity': G.nodes[node]['first_activity'],
            'last_activity': G.nodes[node]['last_activity'],
        }
    
    # Convert to DataFrame
    metrics_df = pd.DataFrame.from_dict(metrics, orient='index')
    metrics_df.index.name = 'user'
    metrics_df.reset_index(inplace=True)
    
    # Add activity type breakdown
    activity_types = []
    for node in G.nodes():
        types = G.nodes[node]['activity_types']
        activity_types.append({
            'user': node,
            'issues_created': types.get('issue_created', 0),
            'prs_created': types.get('pr_created', 0),
            'pr_reviews': sum(1 for t in types.keys() if 'pr_review' in t),
            'comments': sum(1 for t in types.keys() if 'comment' in t),
            'discussions': sum(1 for t in types.keys() if 'discussion' in t),
            'mentions': sum(1 for t in types.keys() if 'mentioned' in t)
        })
    
    activity_df = pd.DataFrame(activity_types)
    metrics_df = metrics_df.merge(activity_df, on='user', how='left')
    
    return metrics_df

def create_network_visualizations(G: nx.Graph, sna_metrics: pd.DataFrame, df: pd.DataFrame):
    """Create comprehensive network visualizations"""
    if G.number_of_nodes() == 0 or sna_metrics.empty:
        print("No data available for visualization")
        return
    
    # Set up the plotting grid
    fig = plt.figure(figsize=(20, 16))
    
    # 1. Activity Distribution
    plt.subplot(3, 3, 1)
    activity_counts = sna_metrics['activity_count'].value_counts().sort_index()
    plt.bar(activity_counts.index, activity_counts.values, alpha=0.7)
    plt.title('Distribution of User Activity Counts')
    plt.xlabel('Activity Count')
    plt.ylabel('Number of Users')
    
    # 2. Centrality Comparison
    plt.subplot(3, 3, 2)
    centrality_cols = ['betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality']
    centrality_data = sna_metrics[centrality_cols].fillna(0)
    plt.boxplot([centrality_data[col] for col in centrality_cols], labels=centrality_cols)
    plt.title('Centrality Measures Distribution')
    plt.ylabel('Centrality Value')
    plt.xticks(rotation=45)
    
    # 3. Activity Types Breakdown
    plt.subplot(3, 3, 3)
    activity_cols = ['issues_created', 'prs_created', 'pr_reviews', 'comments', 'discussions', 'mentions']
    activity_sum = sna_metrics[activity_cols].sum()
    plt.pie(activity_sum.values, labels=activity_sum.index, autopct='%1.1f%%')
    plt.title('Activity Types Distribution')
    
    # 4. Top Users by Different Metrics
    plt.subplot(3, 3, 4)
    top_users = sna_metrics.nlargest(10, 'activity_count')
    plt.barh(top_users['user'], top_users['activity_count'])
    plt.title('Top 10 Users by Activity Count')
    plt.xlabel('Activity Count')
    
    # 5. Network Density Over Time
    plt.subplot(3, 3, 5)
    if not df.empty:
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        daily_activity = df.groupby('date').size()
        plt.plot(daily_activity.index, daily_activity.values, marker='o')
        plt.title('Daily Activity Over Time')
        plt.xlabel('Date')
        plt.ylabel('Activity Count')
        plt.xticks(rotation=45)
    
    # 6. Clustering Coefficient Distribution
    plt.subplot(3, 3, 6)
    plt.hist(sna_metrics['clustering_coefficient'].fillna(0), bins=20, alpha=0.7)
    plt.title('Clustering Coefficient Distribution')
    plt.xlabel('Clustering Coefficient')
    plt.ylabel('Number of Users')
    
    # 7. Degree Distribution
    plt.subplot(3, 3, 7)
    degree_counts = sna_metrics['degree'].value_counts().sort_index()
    plt.loglog(degree_counts.index, degree_counts.values, 'o-')
    plt.title('Degree Distribution (Log-Log Scale)')
    plt.xlabel('Degree')
    plt.ylabel('Number of Users')
    
    # 8. Centrality Correlation
    plt.subplot(3, 3, 8)
    plt.scatter(sna_metrics['betweenness_centrality'], sna_metrics['closeness_centrality'], alpha=0.6)
    plt.title('Betweenness vs Closeness Centrality')
    plt.xlabel('Betweenness Centrality')
    plt.ylabel('Closeness Centrality')
    
    # 9. Network Summary Statistics
    plt.subplot(3, 3, 9)
    plt.axis('off')
    stats_text = f"""
Network Summary:
Nodes: {G.number_of_nodes()}
Edges: {G.number_of_edges()}
Density: {nx.density(G):.3f}
Avg Clustering: {nx.average_clustering(G):.3f}
Avg Path Length: {nx.average_shortest_path_length(G) if nx.is_connected(G) else 'N/A'}
Connected Components: {nx.number_connected_components(G)}
    """
    plt.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
    
    plt.tight_layout()
    plt.show()

def export_data(df: pd.DataFrame, sna_metrics: pd.DataFrame, G: nx.Graph, contributors: List[str], 
                repo_owner: str, repo_name: str, days_back: int, since_date: str, until_date: str):
    """Export all data to CSV files"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Export raw activity data
    if not df.empty:
        output_path = os.path.join(data_dir, f'cobalt_{repo_name}_raw_activity_{timestamp}.csv')
        df.to_csv(output_path, index=False)
        print(f"Exported raw activity data: {output_path}")
    
    # Export SNA metrics
    if not sna_metrics.empty:
        output_path = os.path.join(data_dir, f'cobalt_{repo_name}_sna_metrics_{timestamp}.csv')
        sna_metrics.to_csv(output_path, index=False)
        print(f"Exported SNA metrics: {output_path}")
    
    # Export network edges
    if G.number_of_nodes() != 0:
        edges_df = pd.DataFrame(list(G.edges(data=True)), columns=['source', 'target', 'attributes'])
        edges_df['type'] = edges_df['attributes'].apply(lambda x: x.get('type', ''))
        edges_df['created_at'] = edges_df['attributes'].apply(lambda x: x.get('created_at', ''))
        edges_df['title'] = edges_df['attributes'].apply(lambda x: x.get('title', ''))
        edges_df = edges_df.drop('attributes', axis=1)
        output_path = os.path.join(data_dir, f'cobalt_{repo_name}_network_edges_{timestamp}.csv')
        edges_df.to_csv(output_path, index=False)
        print(f"Exported network edges: {output_path}")
    
    # Export summary report
    summary = {
        'analysis_date': datetime.datetime.now().isoformat(),
        'repository': f'{repo_owner}/{repo_name}',
        'analysis_period_days': days_back,
        'since_date': since_date,
        'until_date': until_date,
        'total_contributors': len(contributors),
        'total_activities': len(df) if not df.empty else 0,
        'network_nodes': G.number_of_nodes() if G.number_of_nodes() != 0 else 0,
        'network_edges': G.number_of_edges() if G.number_of_nodes() != 0 else 0,
        'network_density': nx.density(G) if G.number_of_nodes() != 0 else 0,
        'avg_clustering': nx.average_clustering(G) if G.number_of_nodes() != 0 else 0,
        'connected_components': nx.number_connected_components(G) if G.number_of_nodes() != 0 else 0
    }
    
    summary_df = pd.DataFrame([summary])
    output_path = os.path.join(data_dir, f'cobalt_{repo_name}_analysis_summary_{timestamp}.csv')
    summary_df.to_csv(output_path, index=False)
    print(f"Exported analysis summary: {output_path}")

def generate_insights(sna_metrics: pd.DataFrame, G: nx.Graph, df: pd.DataFrame):
    """Generate insights and recommendations from the analysis"""
    if sna_metrics.empty or G.number_of_nodes() == 0:
        print("No data available for insights")
        return
    
    print("=" * 60)
    print("KEY INSIGHTS AND RECOMMENDATIONS")
    print("=" * 60)
    
    # Top contributors
    top_contributors = sna_metrics.nlargest(3, 'activity_count')
    print(f"\n🏆 TOP CONTRIBUTORS:")
    for _, user in top_contributors.iterrows():
        print(f"  • {user['user']}: {user['activity_count']} activities")
    
    # Most central users
    most_central = sna_metrics.nlargest(3, 'betweenness_centrality')
    print(f"\n🔗 MOST CENTRAL USERS (Information Brokers):")
    for _, user in most_central.iterrows():
        print(f"  • {user['user']}: {user['betweenness_centrality']:.3f} betweenness centrality")
    
    # Network health indicators
    density = nx.density(G)
    avg_clustering = nx.average_clustering(G)
    components = nx.number_connected_components(G)
    
    print(f"\n📊 NETWORK HEALTH INDICATORS:")
    print(f"  • Network Density: {density:.3f} ({'High' if density > 0.1 else 'Medium' if density > 0.05 else 'Low'} collaboration)")
    print(f"  • Average Clustering: {avg_clustering:.3f} ({'Strong' if avg_clustering > 0.3 else 'Moderate' if avg_clustering > 0.1 else 'Weak'} community structure)")
    print(f"  • Connected Components: {components} ({'Good' if components == 1 else 'Fragmented'} network)")
    
    # Activity patterns
    if not df.empty:
        activity_by_type = df['type'].value_counts()
        print(f"\n📈 ACTIVITY PATTERNS:")
        for activity_type, count in activity_by_type.head().items():
            print(f"  • {activity_type}: {count} activities")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if density < 0.05:
        print("  • Consider initiatives to increase cross-team collaboration")
    
    if components > 1:
        print("  • Identify and bridge isolated team members or groups")
    
    if avg_clustering < 0.1:
        print("  • Encourage more focused team interactions and discussions")
    
    # Identify potential bottlenecks
    high_betweenness = sna_metrics[sna_metrics['betweenness_centrality'] > sna_metrics['betweenness_centrality'].quantile(0.9)]
    if len(high_betweenness) > 0:
        print(f"  • Monitor high-centrality users for potential bottlenecks: {', '.join(high_betweenness['user'].tolist())}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 