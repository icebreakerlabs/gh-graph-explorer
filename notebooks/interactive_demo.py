#!/usr/bin/env python3
"""
Interactive Crypto Repository Analysis Demo

This script demonstrates the interactive features of the crypto repository analyzer
without requiring Jupyter notebook. It creates static versions of the interactive plots
and shows how to filter data programmatically.
"""

import os
import sys
sys.path.append('.')

from interactive_crypto_analyzer import InteractiveCryptoAnalyzer
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def demo_interactive_features():
    """Demonstrate the interactive analysis features"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return
    
    print("🎛️ Interactive Crypto Repository Analysis Demo")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = InteractiveCryptoAnalyzer(github_token)
    
    # Load data
    if not analyzer.load_existing_data():
        print("❌ Could not load analysis data")
        print("💡 Please run crypto_repo_analyzer.py first to generate data")
        return
    
    print(f"\n📊 Dataset Overview:")
    print(f"   Total records: {len(analyzer.data)}")
    print(f"   Repositories: {analyzer.data['repo_full_name'].nunique()}")
    print(f"   Contributors: {analyzer.data['source'].nunique()}")
    print(f"   Date range: {analyzer.data['created_at'].min().date()} to {analyzer.data['created_at'].max().date()}")
    
    # Get unique repositories
    repos = sorted(analyzer.data['repo_full_name'].unique())
    print(f"\n🏛️ Available Repositories:")
    for i, repo in enumerate(repos, 1):
        repo_data = analyzer.data[analyzer.data['repo_full_name'] == repo]
        print(f"   {i}. {repo} ({len(repo_data)} activities, {repo_data['source'].nunique()} contributors)")
    
    # Demo filtering
    print(f"\n🔍 Demo: Filtering to first 2 repositories")
    selected_repos = repos[:2]
    date_range = (analyzer.data['created_at'].min().date(), analyzer.data['created_at'].max().date())
    activity_types = list(analyzer.data['type'].unique())
    
    filtered_data = analyzer.filter_data(selected_repos, date_range, activity_types)
    print(f"   Filtered data: {len(filtered_data)} records")
    
    # Create sample visualizations
    print(f"\n📈 Creating Interactive Visualizations...")
    
    try:
        # 1. Network plot
        print("   Creating network visualization...")
        network_fig = analyzer.create_interactive_network_plot(filtered_data)
        network_fig.write_html("data/interactive_network_demo.html")
        print("   ✅ Network plot saved to data/interactive_network_demo.html")
        
        # 2. Contribution stats
        print("   Creating contribution statistics...")
        contrib_fig = analyzer.create_contribution_stats_plot(filtered_data)
        contrib_fig.write_html("data/interactive_contributions_demo.html")
        print("   ✅ Contribution stats saved to data/interactive_contributions_demo.html")
        
        # 3. Activity timeline
        print("   Creating activity timeline...")
        timeline_fig = analyzer.create_activity_timeline_plot(filtered_data)
        timeline_fig.write_html("data/interactive_timeline_demo.html")
        print("   ✅ Timeline plot saved to data/interactive_timeline_demo.html")
        
        # 4. Repository comparison
        print("   Creating repository comparison...")
        repo_fig = analyzer.create_repository_comparison_plot(filtered_data)
        repo_fig.write_html("data/interactive_repo_comparison_demo.html")
        print("   ✅ Repository comparison saved to data/interactive_repo_comparison_demo.html")
        
        print(f"\n🎉 Demo Complete!")
        print(f"   Open the HTML files in your browser to see the interactive visualizations")
        print(f"   Or run the Jupyter notebook 'interactive-crypto-dashboard.ipynb' for full interactivity")
        
    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()

def show_repository_stats():
    """Show detailed stats for each repository"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return
    
    analyzer = InteractiveCryptoAnalyzer(github_token)
    
    if not analyzer.load_existing_data():
        print("❌ Could not load analysis data")
        return
    
    print("\n📊 Detailed Repository Statistics")
    print("=" * 40)
    
    for repo in sorted(analyzer.data['repo_full_name'].unique()):
        repo_data = analyzer.data[analyzer.data['repo_full_name'] == repo]
        
        print(f"\n🏛️ {repo}")
        print(f"   Activities: {len(repo_data)}")
        print(f"   Contributors: {repo_data['source'].nunique()}")
        print(f"   Activity types: {', '.join(repo_data['type'].unique())}")
        print(f"   Date range: {repo_data['created_at'].min().date()} to {repo_data['created_at'].max().date()}")
        
        # Top contributors
        top_contributors = repo_data['source'].value_counts().head(3)
        print(f"   Top contributors:")
        for contributor, count in top_contributors.items():
            print(f"     - {contributor}: {count} activities")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_repository_stats()
    else:
        demo_interactive_features() 