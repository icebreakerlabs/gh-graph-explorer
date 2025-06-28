#!/usr/bin/env python3
"""
Extended Cobalt & Columbo Repository Social Network Analysis

This script analyzes all user activity on both the icebreakerlabs/cobalt and icebreakerlabs/columbo 
repositories over the past 6 months using social network analysis to understand team collaboration 
patterns and engineering metrics across both projects.

Features:
1. Analyzes both cobalt and columbo repositories
2. 6-month analysis period for comprehensive insights
3. Cross-repository collaboration analysis
4. Comparative insights between projects
5. Generates comprehensive visualizations and CSV exports
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
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

class ExtendedCobaltAnalyzer:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.repositories = [
            {'owner': 'icebreakerlabs', 'repo': 'cobalt'},
            {'owner': 'icebreakerlabs', 'repo': 'columbo'}
            # Add more repositories here:
            # {'owner': 'your-org', 'repo': 'your-repo'},
            # {'owner': 'another-org', 'repo': 'another-repo'}
        ]
    
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
    
    def get_repo_collaborators(self, owner: str, repo: str) -> List[str]:
        """Get all collaborators (including those who might not have commits)"""
        url = f'https://api.github.com/repos/{owner}/{repo}/collaborators'
        collaborators = []
        
        try:
            while url:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    collaborators.extend([user['login'] for user in data])
                    
                    # Check for next page
                    if 'next' in response.links:
                        url = response.links['next']['url']
                    else:
                        url = None
                else:
                    print(f"Error fetching collaborators for {owner}/{repo}: {response.status_code}")
                    break
        except Exception as e:
            print(f"Exception fetching collaborators for {owner}/{repo}: {e}")
        
        return collaborators
    
    def get_recent_activity_users(self, owner: str, repo: str, days_back: int = 180) -> List[str]:
        """Get users who have been active in the repository recently"""
        since_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Search for recent issues, PRs, and comments
        search_queries = [
            f'repo:{owner}/{repo} updated:>={since_date}',
            f'repo:{owner}/{repo} is:pr updated:>={since_date}',
            f'repo:{owner}/{repo} is:issue updated:>={since_date}'
        ]
        
        users = set()
        
        for query in search_queries:
            url = f'https://api.github.com/search/issues?q={query}&per_page=100'
            
            try:
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        if 'user' in item:
                            users.add(item['user']['login'])
                        if 'assignee' in item and item['assignee']:
                            users.add(item['assignee']['login'])
                else:
                    print(f"Error searching for recent activity in {owner}/{repo}: {response.status_code}")
            except Exception as e:
                print(f"Exception searching for recent activity in {owner}/{repo}: {e}")
        
        return list(users)
    
    def discover_all_users(self) -> Dict[str, List[str]]:
        """Discover all users across both repositories"""
        all_users = {}
        
        for repo_info in self.repositories:
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            print(f"\nDiscovering users for {owner}/{repo}...")
            
            # Get different types of users
            contributors = self.get_repo_contributors(owner, repo)
            collaborators = self.get_repo_collaborators(owner, repo)
            recent_users = self.get_recent_activity_users(owner, repo, 180)  # 6 months
            
            # Combine all users
            repo_users = list(set(contributors + collaborators + recent_users))
            all_users[f"{owner}/{repo}"] = repo_users
            
            print(f"  Contributors: {len(contributors)}")
            print(f"  Collaborators: {len(collaborators)}")
            print(f"  Recent activity users: {len(recent_users)}")
            print(f"  Total unique users: {len(repo_users)}")
        
        return all_users
    
    def create_multi_repo_config(self, users_by_repo: Dict[str, List[str]]) -> str:
        """Create configuration for multiple repositories"""
        config = []
        summary = {}
        
        for repo_full_name, users in users_by_repo.items():
            owner, repo = repo_full_name.split('/')
            
            for user in users:
                config.append({
                    "username": user,
                    "owner": owner,
                    "repo": repo
                })
            
            summary[repo_full_name] = {
                'user_count': len(users),
                'users': users
            }
        
        # Get the project root directory
        try:
            # For script execution
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            # For notebook execution
            project_root = os.path.dirname(os.getcwd())
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        config_path = os.path.join(project_root, f"data/extended_cobalt_config_{timestamp}.json")
        summary_path = os.path.join(project_root, f"data/extended_cobalt_summary_{timestamp}.json")
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Created configuration with {len(config)} user-repo pairs")
        print(f"Configuration saved: {config_path}")
        print(f"Summary saved: {summary_path}")
        
        return config_path, summary_path
    
    def collect_github_data(self, config_path: str, since_date: str, until_date: str) -> str:
        """Collect GitHub data using the existing tool"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"data/extended_cobalt_activity_{timestamp}.csv"
        
        # Get the project root directory
        try:
            # For script execution
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except NameError:
            # For notebook execution
            project_root = os.path.dirname(os.getcwd())
        
        cmd = [
            "uv", "run", os.path.join(project_root, "main.py"), "collect",
            "--repos", config_path,
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
        print(f"Repositories: {df['repo_full_name'].unique()}")
        print(f"Activity types: {df['type'].value_counts().to_dict()}")
        
        return df
    
    def build_social_network(self, df: pd.DataFrame) -> nx.Graph:
        """Build a social network graph from the activity data"""
        G = nx.Graph()
        
        if df.empty:
            return G
        
        # Add nodes for all users with repository information
        for _, row in df.iterrows():
            source = row['source']
            repo = row['repo_full_name']
            
            if source and pd.notna(source):
                if source in G.nodes:
                    # Update existing node
                    if 'repos' not in G.nodes[source]:
                        G.nodes[source]['repos'] = set()
                    G.nodes[source]['repos'].add(repo)
                else:
                    # Create new node
                    G.add_node(source, repos={repo})
            
            # Add target if exists
            target = row.get('target')
            if target and pd.notna(target) and target != source:
                if target in G.nodes:
                    if 'repos' not in G.nodes[target]:
                        G.nodes[target]['repos'] = set()
                    G.nodes[target]['repos'].add(repo)
                else:
                    G.add_node(target, repos={repo})
        
        # Add edges based on interactions
        for _, row in df.iterrows():
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
                        'repo': row['repo_full_name']
                    })
                else:
                    # Create new edge
                    G.add_edge(source, target, 
                             weight=1,
                             interactions=[{
                                 'type': row['type'],
                                 'created_at': row['created_at'],
                                 'repo': row['repo_full_name']
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
                if subgraph.number_of_edges() > 0:
                    eig_cent = nx.eigenvector_centrality_numpy(subgraph)
                    eigenvector_centrality.update(eig_cent)
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
            repos = node_data.get('repos', set())
            
            metrics[node] = {
                'user': node,
                'degree_centrality': degree_centrality.get(node, 0),
                'betweenness_centrality': betweenness_centrality.get(node, 0),
                'closeness_centrality': closeness_centrality.get(node, 0),
                'eigenvector_centrality': eigenvector_centrality.get(node, 0),
                'clustering_coefficient': clustering.get(node, 0),
                'eccentricity': eccentricity.get(node, float('inf')),
                'degree': G.degree(node),
                'repositories': len(repos),
                'repo_list': ', '.join(sorted(repos)) if repos else '',
                'works_on_cobalt': 'icebreakerlabs/cobalt' in repos if repos else False,
                'works_on_columbo': 'icebreakerlabs/columbo' in repos if repos else False,
                'cross_project': len(repos) > 1 if repos else False
            }
        
        df = pd.DataFrame(list(metrics.values()))
        
        # Add rankings
        df['degree_rank'] = df['degree_centrality'].rank(ascending=False)
        df['betweenness_rank'] = df['betweenness_centrality'].rank(ascending=False)
        df['closeness_rank'] = df['closeness_centrality'].rank(ascending=False)
        df['eigenvector_rank'] = df['eigenvector_centrality'].rank(ascending=False)
        
        return df.sort_values('degree_centrality', ascending=False)
    
    def create_network_visualizations(self, G: nx.Graph, sna_metrics: pd.DataFrame, df: pd.DataFrame):
        """Create comprehensive network visualizations"""
        if G.number_of_nodes() == 0:
            print("No network data to visualize")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 28))
        
        # 1. Cross-Project Network Graph
        plt.subplot(5, 3, 1)
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Color nodes by project participation
        node_colors = []
        for node in G.nodes():
            repos = G.nodes[node].get('repos', set())
            if 'icebreakerlabs/cobalt' in repos and 'icebreakerlabs/columbo' in repos:
                node_colors.append('red')  # Both projects
            elif 'icebreakerlabs/cobalt' in repos:
                node_colors.append('blue')  # Cobalt only
            elif 'icebreakerlabs/columbo' in repos:
                node_colors.append('green')  # Columbo only
            else:
                node_colors.append('gray')  # Neither (shouldn't happen)
        
        nx.draw(G, pos, node_color=node_colors, node_size=100, 
                with_labels=False, alpha=0.7)
        plt.title('Cross-Project Collaboration Network\n(Red: Both, Blue: Cobalt, Green: Columbo)')
        
        # 2. Top Contributors by Degree Centrality
        plt.subplot(5, 3, 2)
        top_degree = sna_metrics.head(15)
        colors = ['red' if row['cross_project'] else 'blue' if row['works_on_cobalt'] else 'green' 
                 for _, row in top_degree.iterrows()]
        plt.barh(range(len(top_degree)), top_degree['degree_centrality'], color=colors)
        plt.yticks(range(len(top_degree)), top_degree['user'])
        plt.xlabel('Degree Centrality')
        plt.title('Top 15 Contributors by Degree Centrality')
        plt.gca().invert_yaxis()
        
        # 3. Top Contributors by Betweenness Centrality
        plt.subplot(5, 3, 3)
        top_betweenness = sna_metrics.nlargest(15, 'betweenness_centrality')
        colors = ['red' if row['cross_project'] else 'blue' if row['works_on_cobalt'] else 'green' 
                 for _, row in top_betweenness.iterrows()]
        plt.barh(range(len(top_betweenness)), top_betweenness['betweenness_centrality'], color=colors)
        plt.yticks(range(len(top_betweenness)), top_betweenness['user'])
        plt.xlabel('Betweenness Centrality')
        plt.title('Top 15 Contributors by Betweenness Centrality')
        plt.gca().invert_yaxis()
        
        # 4. Activity Distribution by Type
        plt.subplot(5, 3, 4)
        activity_counts = df['type'].value_counts()
        plt.pie(activity_counts.values, labels=activity_counts.index, autopct='%1.1f%%')
        plt.title('Activity Distribution by Type')
        
        # 5. Activity Timeline by Repository
        plt.subplot(5, 3, 5)
        df_time = df.copy()
        df_time['date'] = df_time['created_at'].dt.date
        
        for repo in df['repo_full_name'].unique():
            repo_data = df_time[df_time['repo_full_name'] == repo]
            daily_activity = repo_data.groupby('date').size()
            plt.plot(daily_activity.index, daily_activity.values, label=repo.split('/')[-1])
        
        plt.xticks(rotation=45)
        plt.title('Daily Activity Timeline by Repository')
        plt.ylabel('Number of Activities')
        plt.legend()
        
        # 6. Repository Activity Comparison
        plt.subplot(5, 3, 6)
        repo_activity = df['repo_full_name'].value_counts()
        colors = ['blue' if 'cobalt' in repo else 'green' for repo in repo_activity.index]
        plt.bar(range(len(repo_activity)), repo_activity.values, color=colors)
        plt.xticks(range(len(repo_activity)), [repo.split('/')[-1] for repo in repo_activity.index])
        plt.ylabel('Number of Activities')
        plt.title('Total Activity by Repository')
        
        # 7. Cross-Project Users Analysis
        plt.subplot(5, 3, 7)
        cross_project_users = sna_metrics[sna_metrics['cross_project']]
        if not cross_project_users.empty:
            plt.scatter(cross_project_users['degree_centrality'], cross_project_users['betweenness_centrality'])
            plt.xlabel('Degree Centrality')
            plt.ylabel('Betweenness Centrality')
            plt.title(f'Cross-Project Users (n={len(cross_project_users)})')
            
            # Annotate top cross-project users
            top_cross = cross_project_users.head(5)
            for _, user in top_cross.iterrows():
                plt.annotate(user['user'], (user['degree_centrality'], user['betweenness_centrality']),
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
        else:
            plt.text(0.5, 0.5, 'No cross-project users found', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Cross-Project Users')
        
        # 8. Centrality Correlation Heatmap
        plt.subplot(5, 3, 8)
        centrality_cols = ['degree_centrality', 'betweenness_centrality', 'closeness_centrality', 'eigenvector_centrality']
        corr_matrix = sna_metrics[centrality_cols].corr()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Centrality Measures Correlation')
        
        # 9. Project Participation Distribution
        plt.subplot(5, 3, 9)
        participation = {
            'Cobalt Only': sna_metrics['works_on_cobalt'].sum() - sna_metrics['cross_project'].sum(),
            'Columbo Only': sna_metrics['works_on_columbo'].sum() - sna_metrics['cross_project'].sum(),
            'Both Projects': sna_metrics['cross_project'].sum()
        }
        plt.pie(participation.values(), labels=participation.keys(), autopct='%1.1f%%',
                colors=['blue', 'green', 'red'])
        plt.title('Project Participation Distribution')
        
        # 10. Activity by Month
        plt.subplot(5, 3, 10)
        df_monthly = df.copy()
        df_monthly['month'] = df_monthly['created_at'].dt.to_period('M')
        monthly_activity = df_monthly.groupby(['month', 'repo_full_name']).size().unstack(fill_value=0)
        
        if not monthly_activity.empty:
            monthly_activity.plot(kind='bar', stacked=True, color=['blue', 'green'])
            plt.title('Monthly Activity by Repository')
            plt.ylabel('Number of Activities')
            plt.xticks(rotation=45)
            plt.legend(['Cobalt', 'Columbo'] if len(monthly_activity.columns) == 2 else monthly_activity.columns)
        
        # 11. Top Active Users by Repository
        plt.subplot(5, 3, 11)
        cobalt_users = df[df['repo_full_name'] == 'icebreakerlabs/cobalt']['source'].value_counts().head(10)
        columbo_users = df[df['repo_full_name'] == 'icebreakerlabs/columbo']['source'].value_counts().head(10)
        
        # Create side-by-side comparison
        x_pos = np.arange(max(len(cobalt_users), len(columbo_users)))
        width = 0.35
        
        if len(cobalt_users) > 0:
            plt.barh(x_pos[:len(cobalt_users)], cobalt_users.values, width, label='Cobalt', color='blue', alpha=0.7)
        if len(columbo_users) > 0:
            plt.barh(x_pos[:len(columbo_users)] + width, columbo_users.values, width, label='Columbo', color='green', alpha=0.7)
        
        plt.ylabel('Users')
        plt.xlabel('Number of Activities')
        plt.title('Top 10 Most Active Users by Repository')
        plt.legend()
        
        # 12. Network Density Comparison
        plt.subplot(5, 3, 12)
        densities = {}
        for repo in df['repo_full_name'].unique():
            repo_users = set(df[df['repo_full_name'] == repo]['source'].unique())
            if 'target' in df.columns:
                repo_users.update(df[df['repo_full_name'] == repo]['target'].dropna().unique())
            
            if len(repo_users) > 1:
                subgraph = G.subgraph(repo_users)
                densities[repo.split('/')[-1]] = nx.density(subgraph)
        
        if densities:
            repos = list(densities.keys())
            values = list(densities.values())
            colors = ['blue' if 'cobalt' in repo else 'green' for repo in repos]
            plt.bar(repos, values, color=colors)
            plt.ylabel('Network Density')
            plt.title('Network Density by Repository')
        
        # 13. User Activity Distribution
        plt.subplot(5, 3, 13)
        user_activity = df['source'].value_counts()
        plt.hist(user_activity.values, bins=20, alpha=0.7)
        plt.xlabel('Number of Activities per User')
        plt.ylabel('Number of Users')
        plt.title('User Activity Distribution')
        plt.yscale('log')
        
        # 14. Weekly Activity Pattern
        plt.subplot(5, 3, 14)
        df_weekly = df.copy()
        df_weekly['weekday'] = df_weekly['created_at'].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        weekly_pattern = df_weekly.groupby(['weekday', 'repo_full_name']).size().unstack(fill_value=0)
        weekly_pattern = weekly_pattern.reindex(weekday_order)
        
        if not weekly_pattern.empty:
            weekly_pattern.plot(kind='bar', color=['blue', 'green'])
            plt.title('Weekly Activity Pattern')
            plt.ylabel('Number of Activities')
            plt.xticks(rotation=45)
            plt.legend(['Cobalt', 'Columbo'] if len(weekly_pattern.columns) == 2 else weekly_pattern.columns)
        
        # 15. Bridge Users Identification
        plt.subplot(5, 3, 15)
        bridge_users = sna_metrics.nlargest(10, 'betweenness_centrality')
        bridge_users = bridge_users[bridge_users['betweenness_centrality'] > 0]
        
        if not bridge_users.empty:
            colors = ['red' if row['cross_project'] else 'blue' if row['works_on_cobalt'] else 'green' 
                     for _, row in bridge_users.iterrows()]
            plt.barh(range(len(bridge_users)), bridge_users['betweenness_centrality'], color=colors)
            plt.yticks(range(len(bridge_users)), bridge_users['user'])
            plt.xlabel('Betweenness Centrality')
            plt.title('Top Bridge Users')
            plt.gca().invert_yaxis()
        else:
            plt.text(0.5, 0.5, 'No bridge users identified', ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Bridge Users')
        
        plt.tight_layout()
        
        # Save the plot
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(f'data/extended_cobalt_analysis_{timestamp}.png', dpi=300, bbox_inches='tight')
        print(f"Saved visualization: extended_cobalt_analysis_{timestamp}.png")
        plt.show()
    
    def generate_insights(self, sna_metrics: pd.DataFrame, G: nx.Graph, df: pd.DataFrame):
        """Generate insights and recommendations"""
        print("\n" + "="*60)
        print("EXTENDED COBALT & COLUMBO SOCIAL NETWORK ANALYSIS INSIGHTS")
        print("="*60)
        
        if df.empty or sna_metrics.empty:
            print("No data available for analysis")
            return
        
        # Basic statistics
        print(f"\n📊 BASIC STATISTICS")
        print(f"Analysis period: 6 months")
        print(f"Total unique users: {sna_metrics.shape[0]}")
        print(f"Total activities: {len(df)}")
        print(f"Date range: {df['created_at'].min().date()} to {df['created_at'].max().date()}")
        
        # Repository breakdown
        repo_stats = df['repo_full_name'].value_counts()
        for repo, count in repo_stats.items():
            print(f"  {repo}: {count} activities")
        
        # Cross-project analysis
        print(f"\n🔄 CROSS-PROJECT ANALYSIS")
        cross_project_users = sna_metrics[sna_metrics['cross_project']]
        cobalt_only = sna_metrics[sna_metrics['works_on_cobalt'] & ~sna_metrics['cross_project']]
        columbo_only = sna_metrics[sna_metrics['works_on_columbo'] & ~sna_metrics['cross_project']]
        
        print(f"Users working on both projects: {len(cross_project_users)}")
        print(f"Users working on Cobalt only: {len(cobalt_only)}")
        print(f"Users working on Columbo only: {len(columbo_only)}")
        
        if len(cross_project_users) > 0:
            print(f"Cross-project contributors:")
            for _, user in cross_project_users.head(5).iterrows():
                print(f"  - {user['user']} (degree: {user['degree_centrality']:.3f})")
        
        # Network statistics
        print(f"\n🕸️ NETWORK STATISTICS")
        print(f"Network nodes: {G.number_of_nodes()}")
        print(f"Network edges: {G.number_of_edges()}")
        print(f"Network density: {nx.density(G):.3f}")
        print(f"Average clustering coefficient: {nx.average_clustering(G):.3f}")
        print(f"Connected components: {nx.number_connected_components(G)}")
        
        # Top contributors overall
        print(f"\n🌟 TOP CONTRIBUTORS (OVERALL)")
        top_5 = sna_metrics.head(5)
        for i, (_, user) in enumerate(top_5.iterrows(), 1):
            repos = "Both" if user['cross_project'] else ("Cobalt" if user['works_on_cobalt'] else "Columbo")
            print(f"{i}. {user['user']} (degree: {user['degree_centrality']:.3f}, projects: {repos})")
        
        # Repository-specific insights
        print(f"\n📈 REPOSITORY-SPECIFIC INSIGHTS")
        
        for repo in df['repo_full_name'].unique():
            repo_df = df[df['repo_full_name'] == repo]
            repo_name = repo.split('/')[-1].title()
            
            print(f"\n{repo_name}:")
            print(f"  Total activities: {len(repo_df)}")
            print(f"  Unique users: {repo_df['source'].nunique()}")
            print(f"  Most common activity: {repo_df['type'].value_counts().index[0]}")
            
            # Top contributors for this repo
            top_repo_users = repo_df['source'].value_counts().head(3)
            print(f"  Top contributors:")
            for user, count in top_repo_users.items():
                print(f"    - {user}: {count} activities")
        
        # Key insights
        print(f"\n🔍 KEY INSIGHTS")
        
        # Activity patterns
        activity_by_type = df['type'].value_counts()
        print(f"• Most common activity type: {activity_by_type.index[0]} ({activity_by_type.iloc[0]} instances)")
        
        # Network structure
        largest_component = max(nx.connected_components(G), key=len) if G.number_of_nodes() > 0 else set()
        print(f"• Largest connected component: {len(largest_component)} users ({len(largest_component)/G.number_of_nodes()*100:.1f}%)")
        
        # Cross-project collaboration strength
        if len(cross_project_users) > 0:
            avg_cross_centrality = cross_project_users['degree_centrality'].mean()
            avg_single_centrality = sna_metrics[~sna_metrics['cross_project']]['degree_centrality'].mean()
            print(f"• Cross-project users have {avg_cross_centrality/avg_single_centrality:.2f}x higher average centrality")
        
        # Temporal insights
        df_monthly = df.copy()
        df_monthly['month'] = df_monthly['created_at'].dt.to_period('M')
        monthly_trends = df_monthly.groupby(['month', 'repo_full_name']).size().unstack(fill_value=0)
        
        if not monthly_trends.empty and len(monthly_trends) > 1:
            for repo in monthly_trends.columns:
                trend = np.polyfit(range(len(monthly_trends)), monthly_trends[repo], 1)[0]
                repo_name = repo.split('/')[-1].title()
                trend_desc = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
                print(f"• {repo_name} activity trend: {trend_desc} ({trend:.1f} activities/month)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        
        if len(cross_project_users) == 0:
            print("• No cross-project contributors found - consider encouraging collaboration between teams")
        elif len(cross_project_users) < 3:
            print("• Very few cross-project contributors - consider creating more shared initiatives")
        else:
            print("• Good cross-project collaboration - leverage these bridge users for knowledge sharing")
        
        if nx.density(G) < 0.1:
            print("• Low network density suggests opportunities for increased collaboration")
        
        if nx.number_connected_components(G) > 1:
            print("• Multiple disconnected components indicate potential team silos")
            print("• Consider facilitating more cross-team interactions")
        
        # Bridge users (high betweenness centrality)
        bridge_users = sna_metrics.nlargest(3, 'betweenness_centrality')
        if not bridge_users.empty:
            print("• Key bridge users connecting different parts of the network:")
            for _, user in bridge_users.iterrows():
                if user['betweenness_centrality'] > 0:
                    projects = "both projects" if user['cross_project'] else ("Cobalt" if user['works_on_cobalt'] else "Columbo")
                    print(f"  - {user['user']} (betweenness: {user['betweenness_centrality']:.3f}, {projects})")
        
        # Project health comparison
        cobalt_density = 0
        columbo_density = 0
        
        for repo in df['repo_full_name'].unique():
            repo_users = set(df[df['repo_full_name'] == repo]['source'].unique())
            if 'target' in df.columns:
                repo_users.update(df[df['repo_full_name'] == repo]['target'].dropna().unique())
            
            if len(repo_users) > 1:
                subgraph = G.subgraph(repo_users)
                density = nx.density(subgraph)
                if 'cobalt' in repo:
                    cobalt_density = density
                else:
                    columbo_density = density
        
        if cobalt_density > 0 and columbo_density > 0:
            healthier_project = "Cobalt" if cobalt_density > columbo_density else "Columbo"
            print(f"• {healthier_project} shows higher internal collaboration density")
    
    def export_data(self, df: pd.DataFrame, sna_metrics: pd.DataFrame, G: nx.Graph):
        """Export all data to CSV files"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export raw activity data
        if not df.empty:
            output_path = f'data/extended_cobalt_raw_activity_{timestamp}.csv'
            df.to_csv(output_path, index=False)
            print(f"Exported raw activity data: {output_path}")
        
        # Export SNA metrics
        if not sna_metrics.empty:
            output_path = f'data/extended_cobalt_sna_metrics_{timestamp}.csv'
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
            output_path = f'data/extended_cobalt_network_edges_{timestamp}.csv'
            edges_df.to_csv(output_path, index=False)
            print(f"Exported network edges: {output_path}")
        
        # Export cross-project analysis
        cross_project_summary = {
            'metric': ['Total Users', 'Cross-Project Users', 'Cobalt Only', 'Columbo Only', 
                      'Cross-Project Percentage', 'Network Density', 'Connected Components'],
            'value': [
                sna_metrics.shape[0],
                sna_metrics['cross_project'].sum(),
                (sna_metrics['works_on_cobalt'] & ~sna_metrics['cross_project']).sum(),
                (sna_metrics['works_on_columbo'] & ~sna_metrics['cross_project']).sum(),
                f"{sna_metrics['cross_project'].sum() / sna_metrics.shape[0] * 100:.1f}%",
                f"{nx.density(G):.3f}",
                nx.number_connected_components(G)
            ]
        }
        
        summary_df = pd.DataFrame(cross_project_summary)
        output_path = f'data/extended_cobalt_analysis_summary_{timestamp}.csv'
        summary_df.to_csv(output_path, index=False)
        print(f"Exported analysis summary: {output_path}")
    
    def run_full_analysis(self, months_back: int = 6):
        """Run the complete extended analysis"""
        print("Starting Extended Cobalt & Columbo Social Network Analysis")
        print(f"Analysis period: {months_back} months")
        
        # Step 1: Discover all users
        print("\n1. Discovering users across both repositories...")
        users_by_repo = self.discover_all_users()
        
        total_users = sum(len(users) for users in users_by_repo.values())
        unique_users = len(set().union(*users_by_repo.values()))
        print(f"Total user-repo combinations: {total_users}")
        print(f"Unique users across both repos: {unique_users}")
        
        # Step 2: Create configuration
        print("\n2. Creating repository configuration...")
        config_path, summary_path = self.create_multi_repo_config(users_by_repo)
        
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
        self.create_network_visualizations(G, sna_metrics, df)
        
        # Step 8: Export data
        print("\n8. Exporting data...")
        self.export_data(df, sna_metrics, G)
        
        # Step 9: Generate insights
        print("\n9. Generating insights...")
        self.generate_insights(sna_metrics, G, df)
        
        print("\nExtended analysis complete!")
        return {
            'data_file': data_file,
            'config_path': config_path,
            'sna_metrics': sna_metrics,
            'network': G,
            'activity_data': df
        }

def main():
    """Main function to run the extended analysis"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        return
    
    # Parse command line arguments
    months_back = 6
    if len(os.sys.argv) > 1:
        try:
            months_back = int(os.sys.argv[1])
        except ValueError:
            print("Error: months_back must be an integer")
            return
    
    # Run analysis
    analyzer = ExtendedCobaltAnalyzer(github_token)
    results = analyzer.run_full_analysis(months_back)
    
    print("\n" + "="*50)
    print("EXTENDED ANALYSIS COMPLETE")
    print("="*50)
    print("Check the data/ directory for:")
    print("- Raw activity data CSV")
    print("- SNA metrics CSV") 
    print("- Network edges CSV")
    print("- Analysis summary CSV")
    print("- Comprehensive visualization PNG")

if __name__ == "__main__":
    main()