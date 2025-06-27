#!/usr/bin/env python3
"""
Crypto Repository Social Network Analysis

This script analyzes multiple crypto repositories from diverse ecosystems using social network analysis 
to understand collaboration patterns across different crypto projects.

Features:
1. Selects 20-30 diverse crypto repositories from different ecosystems
2. Analyzes the past 6 months of activity for each repository
3. Performs comprehensive social network analysis
4. Generates comparative insights across ecosystems
5. Creates visualizations and exports data to CSV files
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
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import warnings
import random
from urllib.parse import urlparse
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

class CryptoRepoAnalyzer:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def load_crypto_repos(self, jsonl_file: str = "../data/exports.jsonl") -> pd.DataFrame:
        """Load crypto repositories from JSONL file"""
        repos = []
        with open(jsonl_file, 'r') as f:
            for line in f:
                repo_data = json.loads(line.strip())
                if 'repo_url' in repo_data and 'eco_name' in repo_data:
                    repos.append({
                        'repo_url': repo_data['repo_url'],
                        'eco_name': repo_data['eco_name'],
                        'name': repo_data.get('name', ''),
                        'description': repo_data.get('description', '')
                    })
        
        return pd.DataFrame(repos)
    
    def select_diverse_repos(self, repos_df: pd.DataFrame, target_count: int = 25) -> List[Dict[str, str]]:
        """Select diverse repositories from different ecosystems"""
        print("Selecting diverse crypto repositories...")
        
        # Get ecosystem counts (excluding 'General' and very large categories)
        excluded_ecosystems = ['General', 'Ethereum Virtual Machine Stack', 'EVM Compatible L1 and L2']
        
        ecosystem_counts = repos_df[~repos_df['eco_name'].isin(excluded_ecosystems)]['eco_name'].value_counts()
        print(f"Found {len(ecosystem_counts)} unique ecosystems (excluding general categories)")
        
        # Select ecosystems with reasonable number of repos (between 10 and 50k repos)
        suitable_ecosystems = ecosystem_counts[(ecosystem_counts >= 10) & (ecosystem_counts <= 50000)]
        print(f"Found {len(suitable_ecosystems)} suitable ecosystems")
        
        selected_repos = []
        repos_per_ecosystem = max(1, target_count // len(suitable_ecosystems.head(20)))
        
        for ecosystem in suitable_ecosystems.head(20).index:
            ecosystem_repos = repos_df[repos_df['eco_name'] == ecosystem].copy()
            
            # Filter for valid GitHub repos
            ecosystem_repos = ecosystem_repos[ecosystem_repos['repo_url'].str.contains('github.com', na=False)]
            
            if len(ecosystem_repos) > 0:
                # Sample repos from this ecosystem
                sample_size = min(repos_per_ecosystem, len(ecosystem_repos))
                sampled = ecosystem_repos.sample(n=sample_size, random_state=42)
                
                for _, repo in sampled.iterrows():
                    repo_url = repo['repo_url']
                    if 'github.com' in repo_url:
                        # Parse GitHub URL to get owner/repo
                        path_parts = urlparse(repo_url).path.strip('/').split('/')
                        if len(path_parts) >= 2:
                            owner, repo_name = path_parts[0], path_parts[1]
                            selected_repos.append({
                                'owner': owner,
                                'repo': repo_name,
                                'ecosystem': ecosystem,
                                'url': repo_url,
                                'name': repo.get('name', repo_name),
                                'description': repo.get('description', '')
                            })
            
            if len(selected_repos) >= target_count:
                break
        
        print(f"Selected {len(selected_repos)} repositories from {len(set(r['ecosystem'] for r in selected_repos))} ecosystems")
        return selected_repos[:target_count]
    
    def get_repo_contributors(self, owner: str, repo: str) -> List[str]:
        """Get all contributors to a repository"""
        url = f'https://api.github.com/repos/{owner}/{repo}/contributors'
        contributors = []
        
        try:
            while url:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    contributors.extend([user['login'] for user in data])
                    
                    # Check for next page
                    if 'next' in response.links:
                        url = response.links['next']['url']
                    else:
                        url = None
                elif response.status_code == 404:
                    print(f"Repository {owner}/{repo} not found or not accessible")
                    break
                else:
                    print(f"Error fetching contributors for {owner}/{repo}: {response.status_code}")
                    break
        except Exception as e:
            print(f"Exception fetching contributors for {owner}/{repo}: {e}")
        
        return contributors
    
    def create_multi_repo_config(self, selected_repos: List[Dict[str, str]], max_contributors_per_repo: int = 20) -> str:
        """Create configuration for multiple repositories with limited contributors per repo"""
        config = []
        repo_summary = []
        
        for repo_info in selected_repos:
            owner = repo_info['owner']
            repo = repo_info['repo']
            ecosystem = repo_info['ecosystem']
            
            print(f"Processing {owner}/{repo} ({ecosystem})...")
            contributors = self.get_repo_contributors(owner, repo)
            
            if contributors:
                # Limit contributors per repo to avoid overwhelming the analysis
                if len(contributors) > max_contributors_per_repo:
                    contributors = contributors[:max_contributors_per_repo]
                
                for contributor in contributors:
                    config.append({
                        "username": contributor,
                        "owner": owner,
                        "repo": repo
                    })
                
                repo_summary.append({
                    'owner': owner,
                    'repo': repo,
                    'ecosystem': ecosystem,
                    'contributors_count': len(contributors),
                    'url': repo_info['url']
                })
                
                print(f"  Added {len(contributors)} contributors")
            else:
                print(f"  No contributors found")
        
        # Save configuration
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get the current working directory (notebooks) and create absolute paths
        current_dir = os.getcwd()
        config_path = os.path.join(current_dir, f"data/crypto_repos_config_{timestamp}.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save summary
        summary_path = os.path.join(current_dir, f"data/crypto_repos_summary_{timestamp}.json")
        with open(summary_path, 'w') as f:
            json.dump(repo_summary, f, indent=2)
        
        print(f"Created configuration with {len(config)} user-repo pairs")
        print(f"Configuration saved: {config_path}")
        print(f"Summary saved: {summary_path}")
        
        return config_path, summary_path
    
    def collect_github_data(self, config_path: str, since_date: str, until_date: str) -> str:
        """Collect GitHub data using the existing tool"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/crypto_repos_activity_{timestamp}.csv"
        
        # Get the project root directory
        try:
            # For script execution
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            # For notebook execution
            project_root = os.path.dirname(os.getcwd())
        
        cmd = [
            "uv", "run", os.path.join(project_root, "main.py"), "collect",
            "--repos", config_path,  # Use the full path as returned
            "--output", "csv",
            "--output-file", os.path.join(project_root, output_file),
            "--since-iso", since_date,
            "--until-iso", until_date
        ]
        
        print(f"Collecting GitHub activity data from {since_date} to {until_date}...")
        print(f"Running command from: {project_root}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(f"Data collected successfully: {output_file}")
            return output_file
        else:
            print(f"Error collecting data: {result.stderr}")
            return None
    
    def load_and_prepare_data(self, file_path: str) -> pd.DataFrame:
        """Load and prepare the collected data"""
        # If file_path is relative, make it absolute from project root
        if not os.path.isabs(file_path):
            try:
                # For script execution
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            except NameError:
                # For notebook execution
                project_root = os.path.dirname(os.getcwd())
            file_path = os.path.join(project_root, file_path)
        
        if not os.path.exists(file_path):
            print(f"Data file not found: {file_path}")
            return pd.DataFrame()
        
        df = pd.read_csv(file_path)
        
        # Clean and prepare data
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df = df[df['created_at'].notnull()]
        df['title'] = df['title'].fillna('[No Title]')
        
        # Extract repository information from URL
        df['repo_full_name'] = df['url'].str.extract(r'github\.com/([^/]+/[^/]+)')[0]
        
        # Extract owner and repo separately if needed
        df[['owner', 'repo']] = df['repo_full_name'].str.split('/', expand=True)
        
        # Remove duplicates
        df.drop_duplicates(inplace=True)
        
        print(f"Loaded {len(df)} activity records")
        print(f"Date range: {df['created_at'].min()} to {df['created_at'].max()}")
        print(f"Unique users: {df['source'].nunique()}")
        print(f"Unique repositories: {df['repo_full_name'].nunique()}")
        print(f"Activity types: {df['type'].value_counts().to_dict()}")
        
        return df
    
    def build_social_network(self, df: pd.DataFrame) -> nx.Graph:
        """Build a social network graph from the activity data"""
        G = nx.Graph()
        
        if df.empty:
            return G
        
        # Group by repository to build separate networks
        for repo_name, repo_df in df.groupby('repo_full_name'):
            # Add nodes for all users in this repository
            users = set(repo_df['source'].unique())
            if 'target' in repo_df.columns:
                users.update(repo_df['target'].dropna().unique())
            
            for user in users:
                if user and pd.notna(user):
                    G.add_node(user, repos=[repo_name] if repo_name not in G.nodes.get(user, {}).get('repos', []) else G.nodes[user]['repos'] + [repo_name])
            
            # Add edges based on interactions
            for _, row in repo_df.iterrows():
                source = row['source']
                target = row.get('target')
                
                if target and pd.notna(target) and source != target:
                    # Add edge with interaction metadata
                    if G.has_edge(source, target):
                        # Update existing edge
                        G[source][target]['weight'] = G[source][target].get('weight', 0) + 1
                        G[source][target]['interactions'].append({
                            'type': row['type'],
                            'created_at': row['created_at'],
                            'repo': repo_name
                        })
                    else:
                        # Create new edge
                        G.add_edge(source, target, 
                                 weight=1,
                                 interactions=[{
                                     'type': row['type'],
                                     'created_at': row['created_at'],
                                     'repo': repo_name
                                 }])
        
        print(f"Built network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G
    
    def calculate_sna_metrics(self, G: nx.Graph) -> pd.DataFrame:
        """Calculate comprehensive social network analysis metrics"""
        if G.number_of_nodes() == 0:
            return pd.DataFrame()
        
        metrics = {}
        
        # Basic centrality measures
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        
        # Handle eigenvector centrality for disconnected graphs
        try:
            eigenvector_centrality = nx.eigenvector_centrality_numpy(G)
        except:
            print("Computing eigenvector centrality per connected component")
            eigenvector_centrality = {}
            for component in nx.connected_components(G):
                subgraph = G.subgraph(component)
                if subgraph.number_of_edges() > 0 and subgraph.number_of_nodes() > 1:
                    try:
                        eig_cent = nx.eigenvector_centrality_numpy(subgraph)
                        eigenvector_centrality.update(eig_cent)
                    except:
                        # Fallback to regular eigenvector centrality
                        try:
                            eig_cent = nx.eigenvector_centrality(subgraph, max_iter=1000)
                            eigenvector_centrality.update(eig_cent)
                        except:
                            # If all else fails, set to 0
                            for node in component:
                                eigenvector_centrality[node] = 0.0
                else:
                    for node in component:
                        eigenvector_centrality[node] = 0.0
        
        # Clustering coefficient
        clustering = nx.clustering(G)
        
        # Calculate eccentricity safely for disconnected graphs
        eccentricity = {}
        for node in G.nodes():
            try:
                # Get the connected component containing this node
                component = nx.node_connected_component(G, node)
                subgraph = G.subgraph(component)
                if subgraph.number_of_nodes() > 1:
                    eccentricity[node] = nx.eccentricity(subgraph, node)
                else:
                    eccentricity[node] = 0
            except:
                eccentricity[node] = float('inf')
        
        # Compile metrics for each node
        for node in G.nodes():
            node_data = G.nodes[node]
            metrics[node] = {
                'user': node,
                'degree_centrality': degree_centrality.get(node, 0),
                'betweenness_centrality': betweenness_centrality.get(node, 0),
                'closeness_centrality': closeness_centrality.get(node, 0),
                'eigenvector_centrality': eigenvector_centrality.get(node, 0),
                'clustering_coefficient': clustering.get(node, 0),
                'eccentricity': eccentricity.get(node, float('inf')),
                'degree': G.degree(node),
                'repositories': len(node_data.get('repos', [])),
                'repo_list': ', '.join(node_data.get('repos', []))
            }
        
        df = pd.DataFrame(list(metrics.values()))
        
        # Add rankings
        df['degree_rank'] = df['degree_centrality'].rank(ascending=False)
        df['betweenness_rank'] = df['betweenness_centrality'].rank(ascending=False)
        df['closeness_rank'] = df['closeness_centrality'].rank(ascending=False)
        df['eigenvector_rank'] = df['eigenvector_centrality'].rank(ascending=False)
        
        return df.sort_values('degree_centrality', ascending=False)
    
    def create_network_visualizations(self, G: nx.Graph, sna_metrics: pd.DataFrame, df: pd.DataFrame, 
                                    summary_data: List[Dict] = None):
        """Create comprehensive network visualizations"""
        if G.number_of_nodes() == 0:
            print("No network data to visualize")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 24))
        
        # 1. Network Graph
        plt.subplot(4, 3, 1)
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Color nodes by degree centrality
        node_colors = [sna_metrics.set_index('user').loc[node, 'degree_centrality'] 
                      for node in G.nodes() if node in sna_metrics.set_index('user').index]
        
        nx.draw(G, pos, node_color=node_colors, node_size=100, 
                with_labels=False, cmap=plt.cm.viridis, alpha=0.7)
        plt.title('Crypto Repositories Social Network\n(colored by degree centrality)')
        plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.viridis), ax=plt.gca())
        
        # 2. Top Contributors by Degree Centrality
        plt.subplot(4, 3, 2)
        top_degree = sna_metrics.head(15)
        plt.barh(range(len(top_degree)), top_degree['degree_centrality'])
        plt.yticks(range(len(top_degree)), top_degree['user'])
        plt.xlabel('Degree Centrality')
        plt.title('Top 15 Contributors by Degree Centrality')
        plt.gca().invert_yaxis()
        
        # 3. Top Contributors by Betweenness Centrality
        plt.subplot(4, 3, 3)
        top_betweenness = sna_metrics.nlargest(15, 'betweenness_centrality')
        plt.barh(range(len(top_betweenness)), top_betweenness['betweenness_centrality'])
        plt.yticks(range(len(top_betweenness)), top_betweenness['user'])
        plt.xlabel('Betweenness Centrality')
        plt.title('Top 15 Contributors by Betweenness Centrality')
        plt.gca().invert_yaxis()
        
        # 4. Activity Distribution by Type
        plt.subplot(4, 3, 4)
        activity_counts = df['type'].value_counts()
        plt.pie(activity_counts.values, labels=activity_counts.index, autopct='%1.1f%%')
        plt.title('Activity Distribution by Type')
        
        # 5. Activity Timeline
        plt.subplot(4, 3, 5)
        df_time = df.copy()
        df_time['date'] = df_time['created_at'].dt.date
        daily_activity = df_time.groupby('date').size()
        plt.plot(daily_activity.index, daily_activity.values)
        plt.xticks(rotation=45)
        plt.title('Daily Activity Timeline')
        plt.ylabel('Number of Activities')
        
        # 6. Repository Activity Distribution
        plt.subplot(4, 3, 6)
        repo_activity = df['repo_full_name'].value_counts().head(15)
        plt.barh(range(len(repo_activity)), repo_activity.values)
        plt.yticks(range(len(repo_activity)), repo_activity.index)
        plt.xlabel('Number of Activities')
        plt.title('Top 15 Most Active Repositories')
        plt.gca().invert_yaxis()
        
        # 7. Centrality Correlation Heatmap
        plt.subplot(4, 3, 7)
        centrality_cols = ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality']
        corr_matrix = sna_metrics[centrality_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Centrality Measures Correlation')
        
        # 8. Clustering Coefficient Distribution
        plt.subplot(4, 3, 8)
        plt.hist(sna_metrics['clustering_coefficient'], bins=20, alpha=0.7)
        plt.xlabel('Clustering Coefficient')
        plt.ylabel('Number of Users')
        plt.title('Clustering Coefficient Distribution')
        
        # 9. Multi-Repository Users
        plt.subplot(4, 3, 9)
        multi_repo_users = sna_metrics[sna_metrics['repositories'] > 1]
        if not multi_repo_users.empty:
            plt.scatter(multi_repo_users['repositories'], multi_repo_users['degree_centrality'])
            plt.xlabel('Number of Repositories')
            plt.ylabel('Degree Centrality')
            plt.title('Multi-Repository Users')
        else:
            plt.text(0.5, 0.5, 'No multi-repository users found', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Multi-Repository Users')
        
        # 10. Ecosystem Distribution (if summary data available)
        plt.subplot(4, 3, 10)
        if summary_data:
            ecosystem_counts = Counter(item['ecosystem'] for item in summary_data)
            ecosystems = list(ecosystem_counts.keys())[:10]  # Top 10 ecosystems
            counts = [ecosystem_counts[eco] for eco in ecosystems]
            plt.barh(range(len(ecosystems)), counts)
            plt.yticks(range(len(ecosystems)), ecosystems)
            plt.xlabel('Number of Repositories')
            plt.title('Top 10 Ecosystems Analyzed')
            plt.gca().invert_yaxis()
        else:
            plt.text(0.5, 0.5, 'Ecosystem data not available', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Ecosystem Distribution')
        
        # 11. Network Density by Repository
        plt.subplot(4, 3, 11)
        repo_densities = []
        repo_names = []
        for repo_name, repo_df in df.groupby('repo_full_name'):
            users = set(repo_df['source'].unique())
            if 'target' in repo_df.columns:
                users.update(repo_df['target'].dropna().unique())
            
            if len(users) > 1:
                subgraph = G.subgraph(users)
                density = nx.density(subgraph)
                repo_densities.append(density)
                repo_names.append(repo_name.split('/')[-1][:15])  # Truncate long names
        
        if repo_densities:
            plt.barh(range(len(repo_densities)), repo_densities)
            plt.yticks(range(len(repo_densities)), repo_names)
            plt.xlabel('Network Density')
            plt.title('Network Density by Repository')
            plt.gca().invert_yaxis()
        else:
            plt.text(0.5, 0.5, 'No repository density data', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Network Density by Repository')
        
        # 12. Activity by User Type
        plt.subplot(4, 3, 12)
        top_users = sna_metrics.head(10)['user'].tolist()
        user_activity = df[df['source'].isin(top_users)]['source'].value_counts()
        plt.barh(range(len(user_activity)), user_activity.values)
        plt.yticks(range(len(user_activity)), user_activity.index)
        plt.xlabel('Number of Activities')
        plt.title('Top 10 Most Active Users')
        plt.gca().invert_yaxis()
        
        plt.tight_layout()
        
        # Save the plot
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(f'data/crypto_repos_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
        print(f"Saved visualization: crypto_repos_analysis_{timestamp}.png")
        plt.show()
    
    def generate_insights(self, sna_metrics: pd.DataFrame, G: nx.Graph, df: pd.DataFrame, 
                         summary_data: List[Dict] = None):
        """Generate insights and recommendations"""
        print("\n" + "="*60)
        print("CRYPTO REPOSITORIES SOCIAL NETWORK ANALYSIS INSIGHTS")
        print("="*60)
        
        if df.empty or sna_metrics.empty:
            print("No data available for analysis")
            return
        
        # Basic statistics
        print(f"\n📊 BASIC STATISTICS")
        print(f"Total repositories analyzed: {df['repo_full_name'].nunique()}")
        print(f"Total unique users: {sna_metrics.shape[0]}")
        print(f"Total activities: {len(df)}")
        print(f"Date range: {df['created_at'].min().date()} to {df['created_at'].max().date()}")
        
        if summary_data:
            ecosystems = set(item['ecosystem'] for item in summary_data)
            print(f"Ecosystems covered: {len(ecosystems)}")
            print(f"Top ecosystems: {', '.join(list(ecosystems)[:5])}")
        
        # Network statistics
        print(f"\n🕸️ NETWORK STATISTICS")
        print(f"Network nodes: {G.number_of_nodes()}")
        print(f"Network edges: {G.number_of_edges()}")
        print(f"Network density: {nx.density(G):.3f}")
        print(f"Average clustering coefficient: {nx.average_clustering(G):.3f}")
        print(f"Connected components: {nx.number_connected_components(G)}")
        
        # Top contributors
        print(f"\n🌟 TOP CONTRIBUTORS")
        top_5 = sna_metrics.head(5)
        for i, (_, user) in enumerate(top_5.iterrows(), 1):
            print(f"{i}. {user['user']} (degree: {user['degree_centrality']:.3f}, repos: {user['repositories']})")
        
        # Key insights
        print(f"\n🔍 KEY INSIGHTS")
        
        # Cross-ecosystem contributors
        multi_repo_users = sna_metrics[sna_metrics['repositories'] > 1]
        if not multi_repo_users.empty:
            print(f"• {len(multi_repo_users)} users contribute to multiple repositories")
            top_multi = multi_repo_users.nlargest(3, 'repositories')
            for _, user in top_multi.iterrows():
                print(f"  - {user['user']}: {user['repositories']} repositories")
        
        # Activity patterns
        activity_by_type = df['type'].value_counts()
        print(f"• Most common activity: {activity_by_type.index[0]} ({activity_by_type.iloc[0]} instances)")
        
        # Network structure
        largest_component = max(nx.connected_components(G), key=len) if G.number_of_nodes() > 0 else set()
        print(f"• Largest connected component: {len(largest_component)} users ({len(largest_component)/G.number_of_nodes()*100:.1f}%)")
        
        # Repository insights
        most_active_repo = df['repo_full_name'].value_counts().index[0]
        most_active_count = df['repo_full_name'].value_counts().iloc[0]
        print(f"• Most active repository: {most_active_repo} ({most_active_count} activities)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if nx.density(G) < 0.1:
            print("• Low network density suggests opportunities for increased collaboration")
        
        if nx.number_connected_components(G) > 1:
            print("• Multiple disconnected components indicate ecosystem silos")
            print("• Consider facilitating cross-ecosystem knowledge sharing")
        
        if len(multi_repo_users) > 0:
            print("• Multi-repository contributors are valuable bridges between projects")
            print("• Consider highlighting these cross-ecosystem experts")
        
        # Bridge users (high betweenness centrality)
        bridge_users = sna_metrics.nlargest(3, 'betweenness_centrality')
        if not bridge_users.empty:
            print("• Key bridge users connecting different parts of the network:")
            for _, user in bridge_users.iterrows():
                if user['betweenness_centrality'] > 0:
                    print(f"  - {user['user']} (betweenness: {user['betweenness_centrality']:.3f})")
    
    def export_data(self, df: pd.DataFrame, sna_metrics: pd.DataFrame, G: nx.Graph, 
                   summary_data: List[Dict] = None):
        """Export all data to CSV files"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export raw activity data
        if not df.empty:
            output_path = f'data/crypto_repos_raw_activity_{timestamp}.csv'
            df.to_csv(output_path, index=False)
            print(f"Exported raw activity data: {output_path}")
        
        # Export SNA metrics
        if not sna_metrics.empty:
            output_path = f'data/crypto_repos_sna_metrics_{timestamp}.csv'
            sna_metrics.to_csv(output_path, index=False)
            print(f"Exported SNA metrics: {output_path}")
        
        # Export network edges
        if G.number_of_nodes() > 0:
            edges_data = []
            for source, target, data in G.edges(data=True):
                edges_data.append({
                    'source': source,
                    'target': target,
                    'weight': data.get('weight', 1),
                    'interaction_count': len(data.get('interactions', [])),
                    'interaction_types': ', '.join(set(i['type'] for i in data.get('interactions', []))),
                    'repositories': ', '.join(set(i['repo'] for i in data.get('interactions', [])))
                })
            
            edges_df = pd.DataFrame(edges_data)
            output_path = f'data/crypto_repos_network_edges_{timestamp}.csv'
            edges_df.to_csv(output_path, index=False)
            print(f"Exported network edges: {output_path}")
        
        # Export repository summary
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            output_path = f'data/crypto_repos_summary_{timestamp}.csv'
            summary_df.to_csv(output_path, index=False)
            print(f"Exported repository summary: {output_path}")
        
        # Export analysis summary
        summary = {
            'analysis_date': datetime.datetime.now().isoformat(),
            'total_repositories': df['repo_full_name'].nunique() if not df.empty else 0,
            'total_activities': len(df) if not df.empty else 0,
            'total_users': sna_metrics.shape[0] if not sna_metrics.empty else 0,
            'network_nodes': G.number_of_nodes() if G.number_of_nodes() > 0 else 0,
            'network_edges': G.number_of_edges() if G.number_of_nodes() > 0 else 0,
            'network_density': nx.density(G) if G.number_of_nodes() > 0 else 0,
            'avg_clustering': nx.average_clustering(G) if G.number_of_nodes() > 0 else 0,
            'connected_components': nx.number_connected_components(G) if G.number_of_nodes() > 0 else 0,
            'ecosystems_count': len(set(item['ecosystem'] for item in summary_data)) if summary_data else 0
        }
        
        summary_df = pd.DataFrame([summary])
        output_path = f'data/crypto_repos_analysis_summary_{timestamp}.csv'
        summary_df.to_csv(output_path, index=False)
        print(f"Exported analysis summary: {output_path}")
    
    def run_full_analysis(self, months_back: int = 6, target_repo_count: int = 25):
        """Run the complete crypto repositories analysis"""
        print("Starting Crypto Repositories Social Network Analysis")
        print(f"Analysis period: {months_back} months")
        print(f"Target repositories: {target_repo_count}")
        
        # Step 1: Load and select repositories
        print("\n1. Loading crypto repositories data...")
        repos_df = self.load_crypto_repos()
        selected_repos = self.select_diverse_repos(repos_df, target_repo_count)
        
        # Step 2: Create configuration
        print("\n2. Creating repository configuration...")
        config_path, summary_path = self.create_multi_repo_config(selected_repos)
        
        # Load summary data for later use
        with open(summary_path, 'r') as f:
            summary_data = json.load(f)
        
        # Step 3: Collect data
        print("\n3. Collecting GitHub activity data...")
        since_date = (datetime.datetime.now() - datetime.timedelta(days=months_back*30)).strftime('%Y-%m-%d')
        until_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        data_file = self.collect_github_data(config_path, since_date, until_date)
        
        if not data_file:
            print("Failed to collect data. Exiting.")
            return
        
        # Step 4: Load and prepare data
        print("\n4. Loading and preparing data...")
        df = self.load_and_prepare_data(data_file)
        
        if df.empty:
            print("No data available for analysis. Exiting.")
            return
        
        # Step 5: Build social network
        print("\n5. Building social network graph...")
        G = self.build_social_network(df)
        
        # Step 6: Calculate SNA metrics
        print("\n6. Calculating SNA metrics...")
        sna_metrics = self.calculate_sna_metrics(G)
        
        # Step 7: Create visualizations
        print("\n7. Creating visualizations...")
        self.create_network_visualizations(G, sna_metrics, df, summary_data)
        
        # Step 8: Export data
        print("\n8. Exporting data...")
        self.export_data(df, sna_metrics, G, summary_data)
        
        # Step 9: Generate insights
        print("\n9. Generating insights...")
        self.generate_insights(sna_metrics, G, df, summary_data)
        
        print("\nCrypto repositories analysis complete!")
        return {
            'data_file': data_file,
            'config_path': config_path,
            'summary_data': summary_data,
            'sna_metrics': sna_metrics,
            'network': G,
            'activity_data': df
        }

def main():
    """Main function to run the crypto repositories analysis"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return
    
    # Parse command line arguments
    months_back = 6
    target_repo_count = 25
    
    if len(os.sys.argv) > 1:
        try:
            months_back = int(os.sys.argv[1])
        except ValueError:
            print("Error: months_back must be an integer")
            return
    
    if len(os.sys.argv) > 2:
        try:
            target_repo_count = int(os.sys.argv[2])
        except ValueError:
            print("Error: target_repo_count must be an integer")
            return
    
    # Run analysis
    analyzer = CryptoRepoAnalyzer(github_token)
    results = analyzer.run_full_analysis(months_back, target_repo_count)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print("Check the data/ directory for:")
    print("- Raw activity data CSV")
    print("- SNA metrics CSV")
    print("- Network edges CSV")
    print("- Repository summary CSV")
    print("- Analysis summary CSV")
    print("- Visualization PNG")

if __name__ == "__main__":
    main()