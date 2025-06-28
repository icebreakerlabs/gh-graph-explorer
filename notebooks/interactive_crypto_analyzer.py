#!/usr/bin/env python3
"""
Interactive Crypto Repository Social Network Analysis

This script provides an interactive interface for analyzing crypto repositories with:
- Repository filtering widgets
- Interactive visualizations
- Real-time contribution stats
- Dynamic network exploration
"""

import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import ipywidgets as widgets
from IPython.display import display, HTML
import requests
import json
import os
import datetime
import subprocess
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import warnings
from urllib.parse import urlparse
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

class InteractiveCryptoAnalyzer:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.data = None
        self.sna_metrics = None
        self.network = None
        self.summary_data = None
        
    def load_existing_data(self, data_file: str = None, metrics_file: str = None, summary_file: str = None):
        """Load existing analysis data for interactive exploration"""
        if data_file is None:
            # Find the most recent data files
            data_files = [f for f in os.listdir('data/') if f.startswith('crypto_repos_raw_activity_')]
            if data_files:
                data_file = f"data/{sorted(data_files)[-1]}"
            
        if metrics_file is None:
            metrics_files = [f for f in os.listdir('data/') if f.startswith('crypto_repos_sna_metrics_')]
            if metrics_files:
                metrics_file = f"data/{sorted(metrics_files)[-1]}"
                
        if summary_file is None:
            summary_files = [f for f in os.listdir('data/') if f.startswith('crypto_repos_summary_') and f.endswith('.csv')]
            if summary_files:
                summary_file = f"data/{sorted(summary_files)[-1]}"
        
        # Load data
        if data_file and os.path.exists(data_file):
            self.data = pd.read_csv(data_file)
            # Extract repository information from URL if not present
            if 'repo_full_name' not in self.data.columns:
                self.data['repo_full_name'] = self.data['url'].str.extract(r'github\.com/([^/]+/[^/]+)')[0]
            print(f"✅ Loaded activity data: {len(self.data)} records")
        
        if metrics_file and os.path.exists(metrics_file):
            self.sna_metrics = pd.read_csv(metrics_file)
            print(f"✅ Loaded SNA metrics: {len(self.sna_metrics)} users")
            
        if summary_file and os.path.exists(summary_file):
            self.summary_data = pd.read_csv(summary_file)
            print(f"✅ Loaded repository summary: {len(self.summary_data)} repositories")
        
        if self.data is not None:
            self.data['created_at'] = pd.to_datetime(self.data['created_at'])
            
        return self.data is not None and self.sna_metrics is not None
    
    def create_repository_filter_widget(self):
        """Create interactive widgets for repository filtering"""
        if self.data is None:
            print("❌ No data loaded. Please run load_existing_data() first.")
            return None
            
        # Get unique repositories
        repos = sorted(self.data['repo_full_name'].unique())
        
        # Create multi-select widget
        repo_selector = widgets.SelectMultiple(
            options=repos,
            value=repos[:min(5, len(repos))],  # Select first 5 by default
            description='Repositories:',
            disabled=False,
            layout=widgets.Layout(width='400px', height='200px')
        )
        
        # Create date range selector
        min_date = self.data['created_at'].min().date()
        max_date = self.data['created_at'].max().date()
        
        date_range = widgets.SelectionRangeSlider(
            options=pd.date_range(min_date, max_date, freq='W').date.tolist(),
            index=(0, len(pd.date_range(min_date, max_date, freq='W')) - 1),
            description='Date Range:',
            disabled=False,
            layout=widgets.Layout(width='600px')
        )
        
        # Create activity type filter
        activity_types = sorted(self.data['type'].unique())
        activity_selector = widgets.SelectMultiple(
            options=activity_types,
            value=activity_types,
            description='Activity Types:',
            disabled=False,
            layout=widgets.Layout(width='300px', height='150px')
        )
        
        return {
            'repositories': repo_selector,
            'date_range': date_range,
            'activity_types': activity_selector
        }
    
    def filter_data(self, selected_repos, date_range, activity_types):
        """Filter data based on widget selections"""
        if self.data is None:
            return pd.DataFrame()
            
        filtered_data = self.data[
            (self.data['repo_full_name'].isin(selected_repos)) &
            (self.data['created_at'].dt.date >= date_range[0]) &
            (self.data['created_at'].dt.date <= date_range[1]) &
            (self.data['type'].isin(activity_types))
        ].copy()
        
        return filtered_data
    
    def create_interactive_network_plot(self, filtered_data):
        """Create interactive network visualization with Plotly"""
        if filtered_data.empty:
            return go.Figure().add_annotation(text="No data to display", x=0.5, y=0.5)
        
        # Build network from filtered data
        G = nx.Graph()
        
        # Add nodes and edges
        for _, row in filtered_data.iterrows():
            source = row['source']
            target = row.get('target')
            repo = row['repo_full_name']
            
            if source and pd.notna(source):
                G.add_node(source, repo=repo)
                
            if target and pd.notna(target) and source != target:
                if G.has_edge(source, target):
                    G[source][target]['weight'] = G[source][target].get('weight', 0) + 1
                else:
                    G.add_edge(source, target, weight=1)
        
        if G.number_of_nodes() == 0:
            return go.Figure().add_annotation(text="No network connections to display", x=0.5, y=0.5)
        
        # Calculate layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        # Color map for repositories
        repos = list(set([G.nodes[node].get('repo', 'Unknown') for node in G.nodes()]))
        colors = px.colors.qualitative.Set3[:len(repos)]
        repo_color_map = {repo: colors[i % len(colors)] for i, repo in enumerate(repos)}
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node info
            repo = G.nodes[node].get('repo', 'Unknown')
            degree = G.degree(node)
            node_text.append(f"{node}<br>Repository: {repo}<br>Connections: {degree}")
            node_color.append(repo_color_map[repo])
            node_size.append(min(max(degree * 3, 5), 30))
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[node for node in G.nodes()],
            textposition="middle center",
            textfont=dict(size=8),
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=node_text,
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=1, color='black'),
                opacity=0.8
            ),
            name='Contributors'
        )
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        edge_weights = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(G[edge[0]][edge[1]].get('weight', 1))
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='lightgray'),
            hoverinfo='none',
            mode='lines',
            name='Connections'
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                        title=dict(text='Interactive Repository Collaboration Network', font=dict(size=16)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Hover over nodes to see contributor details",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002,
                            xanchor='left', yanchor='bottom',
                            font=dict(color="gray", size=12)
                        )],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        height=600
                    ))
        
        return fig
    
    def create_contribution_stats_plot(self, filtered_data):
        """Create interactive contribution statistics plot"""
        if filtered_data.empty:
            return go.Figure().add_annotation(text="No data to display", x=0.5, y=0.5)
        
        # Calculate contribution stats
        contrib_stats = filtered_data.groupby(['source', 'repo_full_name']).agg({
            'type': 'count',
            'created_at': ['min', 'max']
        }).reset_index()
        
        contrib_stats.columns = ['contributor', 'repository', 'total_activities', 'first_activity', 'last_activity']
        
        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            labels=list(contrib_stats['repository']) + list(contrib_stats['contributor']),
            parents=[''] * len(contrib_stats['repository'].unique()) + list(contrib_stats['repository']),
            values=[contrib_stats[contrib_stats['repository'] == repo]['total_activities'].sum() 
                   for repo in contrib_stats['repository'].unique()] + list(contrib_stats['total_activities']),
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>Activities: %{value}<extra></extra>',
            maxdepth=2,
        ))
        
        fig.update_layout(
            title="Contribution Distribution by Repository and Contributor",
            height=600
        )
        
        return fig
    
    def create_activity_timeline_plot(self, filtered_data):
        """Create interactive activity timeline"""
        if filtered_data.empty:
            return go.Figure().add_annotation(text="No data to display", x=0.5, y=0.5)
        
        # Prepare timeline data
        timeline_data = filtered_data.copy()
        timeline_data['date'] = timeline_data['created_at'].dt.date
        
        daily_stats = timeline_data.groupby(['date', 'repo_full_name', 'type']).size().reset_index(name='count')
        
        fig = px.line(daily_stats, x='date', y='count', color='repo_full_name', 
                     facet_col='type', facet_col_wrap=3,
                     title='Activity Timeline by Repository and Type',
                     hover_data=['repo_full_name', 'type'])
        
        fig.update_layout(height=800)
        return fig
    
    def create_contributor_comparison_plot(self, filtered_data):
        """Create interactive contributor comparison"""
        if filtered_data.empty:
            return go.Figure().add_annotation(text="No data to display", x=0.5, y=0.5)
        
        # Top contributors analysis
        contrib_analysis = filtered_data.groupby(['source', 'repo_full_name']).agg({
            'type': ['count', 'nunique'],
            'created_at': ['min', 'max']
        }).reset_index()
        
        contrib_analysis.columns = ['contributor', 'repository', 'total_activities', 'activity_types', 'first_activity', 'last_activity']
        contrib_analysis['days_active'] = (contrib_analysis['last_activity'] - contrib_analysis['first_activity']).dt.days + 1
        contrib_analysis['activity_rate'] = contrib_analysis['total_activities'] / contrib_analysis['days_active']
        
        # Create scatter plot
        fig = px.scatter(contrib_analysis, 
                        x='total_activities', 
                        y='activity_rate',
                        size='activity_types',
                        color='repository',
                        hover_data=['contributor', 'days_active'],
                        title='Contributor Activity Analysis',
                        labels={
                            'total_activities': 'Total Activities',
                            'activity_rate': 'Activities per Day',
                            'activity_types': 'Unique Activity Types'
                        })
        
        fig.update_layout(height=600)
        return fig
    
    def create_repository_comparison_plot(self, filtered_data):
        """Create repository comparison visualization"""
        if filtered_data.empty:
            return go.Figure().add_annotation(text="No data to display", x=0.5, y=0.5)
        
        # Repository stats
        repo_stats = filtered_data.groupby('repo_full_name').agg({
            'source': 'nunique',
            'type': ['count', 'nunique'],
            'created_at': ['min', 'max']
        }).reset_index()
        
        repo_stats.columns = ['repository', 'unique_contributors', 'total_activities', 'activity_types', 'first_activity', 'last_activity']
        repo_stats['days_active'] = (repo_stats['last_activity'] - repo_stats['first_activity']).dt.days + 1
        repo_stats['activity_density'] = repo_stats['total_activities'] / repo_stats['days_active']
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Contributors per Repository', 'Activity Types per Repository', 
                          'Total Activities', 'Activity Density'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Add traces
        fig.add_trace(go.Bar(x=repo_stats['repository'], y=repo_stats['unique_contributors'], 
                            name='Contributors'), row=1, col=1)
        fig.add_trace(go.Bar(x=repo_stats['repository'], y=repo_stats['activity_types'], 
                            name='Activity Types'), row=1, col=2)
        fig.add_trace(go.Bar(x=repo_stats['repository'], y=repo_stats['total_activities'], 
                            name='Total Activities'), row=2, col=1)
        fig.add_trace(go.Bar(x=repo_stats['repository'], y=repo_stats['activity_density'], 
                            name='Activity Density'), row=2, col=2)
        
        fig.update_layout(height=800, title_text="Repository Comparison Dashboard", showlegend=False)
        return fig
    
    def create_interactive_dashboard(self):
        """Create the main interactive dashboard"""
        if not self.load_existing_data():
            print("❌ Could not load data. Please run the crypto repository analysis first.")
            return
        
        print("🎛️ Creating Interactive Crypto Repository Analysis Dashboard")
        print("=" * 60)
        
        # Create filter widgets
        filters = self.create_repository_filter_widget()
        if filters is None:
            return
        
        # Create output widget for plots
        output = widgets.Output()
        
        def update_plots(*args):
            """Update all plots when filters change"""
            with output:
                output.clear_output(wait=True)
                
                # Get filter values
                selected_repos = list(filters['repositories'].value)
                date_range = filters['date_range'].value
                activity_types = list(filters['activity_types'].value)
                
                if not selected_repos:
                    print("⚠️ Please select at least one repository")
                    return
                
                # Filter data
                filtered_data = self.filter_data(selected_repos, date_range, activity_types)
                
                print(f"📊 Showing data for {len(selected_repos)} repositories")
                print(f"📅 Date range: {date_range[0]} to {date_range[1]}")
                print(f"📈 Filtered to {len(filtered_data)} activities")
                print("-" * 40)
                
                if filtered_data.empty:
                    print("❌ No data matches the current filters")
                    return
                
                # Create and display plots
                try:
                    # Network plot
                    network_fig = self.create_interactive_network_plot(filtered_data)
                    network_fig.show()
                    
                    # Contribution stats
                    contrib_fig = self.create_contribution_stats_plot(filtered_data)
                    contrib_fig.show()
                    
                    # Activity timeline
                    timeline_fig = self.create_activity_timeline_plot(filtered_data)
                    timeline_fig.show()
                    
                    # Contributor comparison
                    contributor_fig = self.create_contributor_comparison_plot(filtered_data)
                    contributor_fig.show()
                    
                    # Repository comparison
                    repo_fig = self.create_repository_comparison_plot(filtered_data)
                    repo_fig.show()
                    
                except Exception as e:
                    print(f"❌ Error creating plots: {e}")
        
        # Connect widgets to update function
        filters['repositories'].observe(update_plots, names='value')
        filters['date_range'].observe(update_plots, names='value')
        filters['activity_types'].observe(update_plots, names='value')
        
        # Display widgets
        print("🎮 Use the controls below to filter and explore the data:")
        display(widgets.VBox([
            widgets.HTML("<h3>🔍 Filter Controls</h3>"),
            widgets.HBox([filters['repositories'], filters['activity_types']]),
            filters['date_range'],
            widgets.HTML("<h3>📊 Interactive Visualizations</h3>"),
            output
        ]))
        
        # Initial plot
        update_plots()
    
    def create_summary_stats_widget(self):
        """Create a summary statistics widget"""
        if self.data is None:
            return widgets.HTML("❌ No data loaded")
        
        total_repos = self.data['repo_full_name'].nunique()
        total_users = self.data['source'].nunique()
        total_activities = len(self.data)
        date_range = f"{self.data['created_at'].min().date()} to {self.data['created_at'].max().date()}"
        
        html_content = f"""
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3>📊 Dataset Summary</h3>
            <ul>
                <li><b>Repositories:</b> {total_repos}</li>
                <li><b>Contributors:</b> {total_users}</li>
                <li><b>Total Activities:</b> {total_activities}</li>
                <li><b>Date Range:</b> {date_range}</li>
            </ul>
        </div>
        """
        
        return widgets.HTML(html_content)

def run_interactive_analysis():
    """Main function to run the interactive analysis"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        return
    
    analyzer = InteractiveCryptoAnalyzer(github_token)
    
    # Display summary
    summary_widget = analyzer.create_summary_stats_widget()
    if summary_widget:
        display(summary_widget)
    
    # Create interactive dashboard
    analyzer.create_interactive_dashboard()

if __name__ == "__main__":
    run_interactive_analysis() 