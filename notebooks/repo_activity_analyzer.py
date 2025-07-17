#!/usr/bin/env python3
"""
GitHub Repository Activity Analyzer

This script analyzes the activity of GitHub repositories by measuring 
the number of commits in the past 3 months for a sample of repositories.
"""

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional
import os
import dotenv

dotenv.load_dotenv()

class RepoActivityAnalyzer:
    def __init__(self, github_token: str):
        """Initialize the analyzer with GitHub token"""
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Calculate date range (3 months ago)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=90)
        self.since_date = self.start_date.strftime('%Y-%m-%d')
        
        print(f"Analyzing commits from {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
    
    def load_jsonl_as_list(self, file_path: str) -> list:
        """Load a JSONL file as a list of dictionaries"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line.strip()))
        return data
    
    def extract_github_info(self, url: str) -> tuple:
        """Extract owner and repo name from GitHub URL"""
        try:
            path = urlparse(url).path.strip('/').split('/')
            if len(path) >= 2:
                return path[0], path[1]
        except:
            pass
        return None, None
    
    def count_commits_since_date(self, owner: str, repo: str) -> int:
        """Count commits in a repository since a specific date"""
        url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        params = {
            'since': self.since_date,
            'per_page': 100  # Maximum per page
        }
        
        total_commits = 0
        
        try:
            while url:
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    commits = response.json()
                    total_commits += len(commits)
                    
                    # Check for next page
                    if 'next' in response.links:
                        url = response.links['next']['url']
                        params = {}  # Clear params for subsequent requests
                    else:
                        url = None
                        
                elif response.status_code == 404:
                    print(f"Repository {owner}/{repo} not found")
                    return -1
                elif response.status_code == 403:
                    print(f"Rate limit exceeded for {owner}/{repo}")
                    return -2
                else:
                    print(f"Error {response.status_code} for {owner}/{repo}")
                    return -3
                    
        except Exception as e:
            print(f"Exception for {owner}/{repo}: {e}")
            return -4
        
        return total_commits
    
    def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get basic repository information"""
        url = f'https://api.github.com/repos/{owner}/{repo}'
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error getting repo info for {owner}/{repo}: {e}")
            return None
    
    def analyze_repositories(self, jsonl_file: str, sample_size: int = 100) -> pd.DataFrame:
        """Analyze repository activity for a sample of repositories"""
        
        # Load repository data
        print("Loading repository data...")
        repos_data = self.load_jsonl_as_list(jsonl_file)
        print(f"Loaded {len(repos_data)} repositories")
        
        # Convert to DataFrame
        df = pd.DataFrame(repos_data)
        
        # Filter for valid GitHub repositories
        github_repos = df[df['repo_url'].str.contains('github.com', na=False)].copy()
        print(f"Found {len(github_repos)} GitHub repositories")
        
        # Extract owner and repo name from URLs
        github_repos[['owner', 'repo']] = github_repos['repo_url'].apply(
            lambda x: pd.Series(self.extract_github_info(x))
        )
        
        # Remove rows where we couldn't extract owner/repo
        github_repos = github_repos.dropna(subset=['owner', 'repo'])
        print(f"Valid GitHub repos: {len(github_repos)}")
        
        # Sample repositories for testing
        sample_repos = github_repos.sample(n=sample_size, random_state=42)
        print(f"Sampled {len(sample_repos)} repositories for analysis")
        
        # Analyze each repository
        results = []
        
        for idx, row in sample_repos.iterrows():
            owner = row['owner']
            repo = row['repo']
            eco_name = row['eco_name']
            repo_url = row['repo_url']
            
            print(f"Analyzing {owner}/{repo} ({eco_name})...")
            
            # Get repo info
            repo_info = self.get_repo_info(owner, repo)
            
            # Count commits
            commit_count = self.count_commits_since_date(owner, repo)
            
            result = {
                'owner': owner,
                'repo': repo,
                'eco_name': eco_name,
                'repo_url': repo_url,
                'commits_past_3_months': commit_count,
                'stars': repo_info.get('stargazers_count', 0) if repo_info else 0,
                'forks': repo_info.get('forks_count', 0) if repo_info else 0,
                'language': repo_info.get('language', 'Unknown') if repo_info else 'Unknown',
                'created_at': repo_info.get('created_at', 'Unknown') if repo_info else 'Unknown',
                'updated_at': repo_info.get('updated_at', 'Unknown') if repo_info else 'Unknown'
            }
            
            results.append(result)
            
            # Rate limiting - pause between requests
            time.sleep(1)
            
            # Progress indicator
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(sample_repos)} repositories")
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Filter out repositories with errors (negative commit counts)
        valid_results = results_df[results_df['commits_past_3_months'] >= 0].copy()
        error_results = results_df[results_df['commits_past_3_months'] < 0].copy()
        
        print(f"\nSuccessfully analyzed: {len(valid_results)} repositories")
        print(f"Errors encountered: {len(error_results)} repositories")
        
        return valid_results, error_results
    
    def generate_summary_stats(self, valid_results: pd.DataFrame) -> dict:
        """Generate summary statistics"""
        summary = {
            'total_repos_analyzed': len(valid_results),
            'total_commits': valid_results['commits_past_3_months'].sum(),
            'avg_commits_per_repo': valid_results['commits_past_3_months'].mean(),
            'median_commits_per_repo': valid_results['commits_past_3_months'].median(),
            'max_commits': valid_results['commits_past_3_months'].max(),
            'min_commits': valid_results['commits_past_3_months'].min(),
            'total_stars': valid_results['stars'].sum(),
            'avg_stars_per_repo': valid_results['stars'].mean()
        }
        
        # Activity categories
        def categorize_activity(commits):
            if commits == 0:
                return 'Inactive'
            elif commits <= 10:
                return 'Low Activity'
            elif commits <= 50:
                return 'Moderate Activity'
            else:
                return 'High Activity'
        
        valid_results['activity_category'] = valid_results['commits_past_3_months'].apply(categorize_activity)
        activity_counts = valid_results['activity_category'].value_counts()
        summary['activity_distribution'] = activity_counts.to_dict()
        
        # Top ecosystems
        eco_stats = valid_results.groupby('eco_name')['commits_past_3_months'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        summary['top_ecosystems'] = eco_stats.head(5).to_dict()
        
        return summary
    
    def save_results(self, valid_results: pd.DataFrame, summary: dict):
        """Save results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results
        output_file = f'repo_activity_analysis_{timestamp}.csv'
        valid_results.to_csv(output_file, index=False)
        print(f"Detailed results saved to: {output_file}")
        
        # Save summary
        summary_file = f'repo_activity_summary_{timestamp}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to: {summary_file}")
        
        return output_file, summary_file
    
    def print_summary(self, valid_results: pd.DataFrame, summary: dict):
        """Print summary to console"""
        print("\n" + "="*60)
        print("REPOSITORY ACTIVITY ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"Analysis Period: {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Repositories Analyzed: {summary['total_repos_analyzed']}")
        print(f"Total Commits (Past 3 Months): {summary['total_commits']}")
        print(f"Average Commits per Repo: {summary['avg_commits_per_repo']:.2f}")
        print(f"Median Commits per Repo: {summary['median_commits_per_repo']:.2f}")
        print(f"Most Active Repo: {valid_results.loc[valid_results['commits_past_3_months'].idxmax(), 'owner']}/{valid_results.loc[valid_results['commits_past_3_months'].idxmax(), 'repo']} ({summary['max_commits']} commits)")
        
        print("\nActivity Distribution:")
        for category, count in summary['activity_distribution'].items():
            percentage = (count / summary['total_repos_analyzed']) * 100
            print(f"  {category}: {count} repos ({percentage:.1f}%)")
        
        print("\nTop 5 Most Active Ecosystems:")
        for eco_name, stats in list(summary['top_ecosystems'].items())[:5]:
            print(f"  {eco_name}: {stats['mean']:.2f} avg commits ({stats['count']} repos)")
        
        print("\nTop 10 Most Active Repositories:")
        top_active = valid_results.nlargest(10, 'commits_past_3_months')
        for _, row in top_active.iterrows():
            print(f"  {row['owner']}/{row['repo']}: {row['commits_past_3_months']} commits ({row['eco_name']})")


def main():
    """Main function to run the analysis"""
    
    # You need to set your GitHub token here
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Replace with your actual token
    
    if GITHUB_TOKEN == "your_github_token_here":
        print("ERROR: Please set your GitHub token in the script!")
        print("You can get a token from: https://github.com/settings/tokens")
        return
    
    # Initialize analyzer
    analyzer = RepoActivityAnalyzer(GITHUB_TOKEN)
    
    # Run analysis
    jsonl_file = "../data/exports.jsonl"
    sample_size = 100
    
    print(f"Starting analysis of {sample_size} repositories...")
    
    try:
        valid_results, error_results = analyzer.analyze_repositories(jsonl_file, sample_size)
        
        if len(valid_results) > 0:
            # Generate summary
            summary = analyzer.generate_summary_stats(valid_results)
            
            # Save results
            output_file, summary_file = analyzer.save_results(valid_results, summary)
            
            # Print summary
            analyzer.print_summary(valid_results, summary)
            
        else:
            print("No valid results to analyze!")
            
    except Exception as e:
        print(f"Error during analysis: {e}")


if __name__ == "__main__":
    main() 