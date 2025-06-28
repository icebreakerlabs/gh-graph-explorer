#!/usr/bin/env python3
"""
Cobalt Repository Analyzer

This script automates the process of discovering contributors and collecting
GitHub activity data for the icebreakerlabs/cobalt repository.
"""

import os
import sys
import json
import requests
import subprocess
import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Add the src directory to the path so we can import from the project
sys.path.append(str(Path(__file__).parent))

class CobaltAnalyzer:
    def __init__(self, github_token: str, repo_owner: str = "icebreakerlabs", repo_name: str = "cobalt"):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_repo_contributors(self) -> List[str]:
        """Get all contributors to the repository"""
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contributors'
        contributors = []
        
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
            else:
                print(f"Error fetching contributors: {response.status_code}")
                break
        
        return contributors
    
    def get_repo_collaborators(self) -> List[str]:
        """Get all collaborators (including those who might not have commits)"""
        url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/collaborators'
        collaborators = []
        
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
                print(f"Error fetching collaborators: {response.status_code}")
                break
        
        return collaborators
    
    def get_recent_activity_users(self, days_back: int = 30) -> List[str]:
        """Get users who have been active in the repository recently"""
        since_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Search for recent issues, PRs, and comments
        search_queries = [
            f'repo:{self.repo_owner}/{self.repo_name} updated:>={since_date}',
            f'repo:{self.repo_owner}/{self.repo_name} is:pr updated:>={since_date}',
            f'repo:{self.repo_owner}/{self.repo_name} is:issue updated:>={since_date}'
        ]
        
        users = set()
        
        for query in search_queries:
            url = f'https://api.github.com/search/issues?q={query}&per_page=100'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    if 'user' in item:
                        users.add(item['user']['login'])
                    if 'assignee' in item and item['assignee']:
                        users.add(item['assignee']['login'])
            else:
                print(f"Error searching for recent activity: {response.status_code}")
        
        return list(users)
    
    def create_repos_config(self, users: List[str], output_path: str = None) -> str:
        """Create repos.json configuration for all users"""
        if output_path is None:
            output_path = f"data/cobalt_{self.repo_name}_repos.json"
        
        config = []
        for user in users:
            config.append({
                "username": user,
                "owner": self.repo_owner,
                "repo": self.repo_name
            })
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return output_path
    
    def collect_github_data(self, config_path: str, since_date: str, until_date: str, output_file: str = None) -> Optional[str]:
        """Collect GitHub data using the existing tool"""
        if output_file is None:
            output_file = f"data/cobalt_{self.repo_name}_activity.csv"
        
        cmd = [
            "uv", "run", "main.py", "collect",
            "--repos", config_path,
            "--output", "csv",
            "--output-file", output_file,
            "--since-iso", since_date,
            "--until-iso", until_date
        ]
        
        print(f"Collecting GitHub activity data from {since_date} to {until_date}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Data collected successfully: {output_file}")
            return output_file
        else:
            print(f"Error collecting data: {result.stderr}")
            return None
    
    def run_full_analysis(self, days_back: int = 30) -> Dict[str, str]:
        """Run the complete analysis pipeline"""
        print(f"Starting analysis of {self.repo_owner}/{self.repo_name}")
        print(f"Analysis period: {days_back} days")
        
        # Step 1: Discover users
        print("\n1. Discovering repository users...")
        contributors = self.get_repo_contributors()
        collaborators = self.get_repo_collaborators()
        recent_users = self.get_recent_activity_users(days_back)
        
        # Combine all users
        all_users = list(set(contributors + collaborators + recent_users))
        print(f"Found {len(all_users)} unique users:")
        print(f"  - Contributors: {len(contributors)}")
        print(f"  - Collaborators: {len(collaborators)}")
        print(f"  - Recent activity: {len(recent_users)}")
        
        # Step 2: Create configuration
        print("\n2. Creating repository configuration...")
        config_path = self.create_repos_config(all_users)
        print(f"Configuration created: {config_path}")
        
        # Step 3: Collect data
        print("\n3. Collecting GitHub activity data...")
        since_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
        until_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        data_file = self.collect_github_data(config_path, since_date, until_date)
        
        return {
            'config_path': config_path,
            'data_file': data_file,
            'users_count': len(all_users),
            'since_date': since_date,
            'until_date': until_date
        }

def main():
    """Main function to run the analysis"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Parse command line arguments
    days_back = 30
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            print("Error: days_back must be an integer")
            sys.exit(1)
    
    # Run analysis
    analyzer = CobaltAnalyzer(github_token)
    results = analyzer.run_full_analysis(days_back)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print(f"Configuration file: {results['config_path']}")
    print(f"Data file: {results['data_file']}")
    print(f"Users analyzed: {results['users_count']}")
    print(f"Date range: {results['since_date']} to {results['until_date']}")
    print("\nNext steps:")
    print("1. Open the Jupyter notebook: notebooks/cobalt-repo-analysis.ipynb")
    print("2. Run all cells to generate visualizations and insights")
    print("3. Check the data/ directory for exported CSV files")

if __name__ == "__main__":
    main() 