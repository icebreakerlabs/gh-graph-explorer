#!/usr/bin/env python3
"""
GitHub Username Activity Analyzer

This script analyzes the GitHub activity of usernames from a CSV file.
It counts commits across repositories for each username and saves results
every 100 usernames with checkpointing to resume from where it left off.
"""

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import sys
from typing import List, Dict, Optional, Tuple
import dotenv

dotenv.load_dotenv()

class GitHubUsernameActivityAnalyzer:
    def __init__(self, github_token: str, checkpoint_file: str = "username_analysis_checkpoint.json",
                 results_file: str = "github_username_activity_results.csv",
                 save_frequency: int = 100):
        """Initialize the analyzer with checkpointing"""
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Calculate date range (3 months ago)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=90)
        self.since_date = self.start_date.strftime('%Y-%m-%d')
        
        # Checkpoint and file management
        self.checkpoint_file = checkpoint_file
        self.results_file = results_file
        self.save_frequency = save_frequency
        
        # Load checkpoint if exists
        self.processed_usernames = self.load_checkpoint()
        
        print(f"Analyzing commits from {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Already processed: {len(self.processed_usernames)} usernames")
        print(f"Checkpoint file: {checkpoint_file}")
        print(f"Results file: {results_file}")
    
    def load_checkpoint(self) -> set:
        """Load processed usernames from checkpoint file"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                    return set(checkpoint_data.get('processed_usernames', []))
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
        return set()
    
    def save_checkpoint(self, processed_usernames: set):
        """Save checkpoint with processed usernames"""
        checkpoint_data = {
            'processed_usernames': list(processed_usernames),
            'last_updated': datetime.now().isoformat(),
            'total_processed': len(processed_usernames)
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
    
    def get_user_info(self, username: str) -> dict:
        """Get basic user information from GitHub API"""
        url = f'https://api.github.com/users/{username}'
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403 and 'rate limit' in response.text.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"Rate limit hit for user info {username}, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                elif response.status_code == 404:
                    print(f"User {username} not found")
                    return None
                else:
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting user info for {username}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting user info for {username}: {e}")
                    return None
        
        return None
    
    def get_user_repositories(self, username: str) -> List[Dict]:
        """Get all repositories for a user"""
        url = f'https://api.github.com/users/{username}/repos'
        params = {
            'per_page': 100,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        repositories = []
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                while url:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        repos = response.json()
                        repositories.extend(repos)
                        
                        # Check for next page
                        if 'next' in response.links:
                            url = response.links['next']['url']
                            params = {}
                        else:
                            url = None
                            
                    elif response.status_code == 403 and 'rate limit' in response.text.lower():
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Rate limit hit for repos {username}, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            break
                        else:
                            return repositories
                    elif response.status_code == 404:
                        print(f"User {username} not found")
                        return []
                    else:
                        print(f"Error {response.status_code} for {username} repos")
                        return []
                
                return repositories
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting repos for {username}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting repos for {username}: {e}")
                    return repositories
        
        return repositories
    
    def count_commits_for_repo(self, owner: str, repo: str) -> int:
        """Count commits in a repository since a specific date"""
        url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        params = {
            'since': self.since_date,
            'per_page': 100
        }
        
        total_commits = 0
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                while url:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        commits = response.json()
                        total_commits += len(commits)
                        
                        # Check for next page
                        if 'next' in response.links:
                            url = response.links['next']['url']
                            params = {}
                        else:
                            url = None
                            
                    elif response.status_code == 404:
                        return 0  # Repo not found or no access
                    elif response.status_code == 403:
                        if 'rate limit' in response.text.lower():
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Rate limit hit for commits {owner}/{repo}, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            return 0  # Access forbidden
                    else:
                        return 0
                
                return total_commits
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception for commits {owner}/{repo}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception for commits {owner}/{repo}: {e}")
                    return 0
        
        return total_commits
    
    def analyze_username_activity(self, username: str) -> dict:
        """Analyze activity for a single username"""
        print(f"Analyzing {username}...")
        
        # Get user info
        user_info = self.get_user_info(username)
        if not user_info:
            return {
                'username': username,
                'user_found': False,
                'total_repos': 0,
                'total_commits_past_3_months': 0,
                'active_repos': 0,
                'avg_commits_per_repo': 0,
                'most_active_repo': None,
                'most_active_repo_commits': 0,
                'user_type': user_info.get('type', 'Unknown') if user_info else 'Unknown',
                'public_repos': user_info.get('public_repos', 0) if user_info else 0,
                'followers': user_info.get('followers', 0) if user_info else 0,
                'created_at': user_info.get('created_at', 'Unknown') if user_info else 'Unknown',
                'processed_at': datetime.now().isoformat()
            }
        
        # Get user repositories
        repositories = self.get_user_repositories(username)
        
        if not repositories:
            return {
                'username': username,
                'user_found': True,
                'total_repos': 0,
                'total_commits_past_3_months': 0,
                'active_repos': 0,
                'avg_commits_per_repo': 0,
                'most_active_repo': None,
                'most_active_repo_commits': 0,
                'user_type': user_info.get('type', 'Unknown'),
                'public_repos': user_info.get('public_repos', 0),
                'followers': user_info.get('followers', 0),
                'created_at': user_info.get('created_at', 'Unknown'),
                'processed_at': datetime.now().isoformat()
            }
        
        # Analyze commits for each repository
        repo_commits = {}
        total_commits = 0
        active_repos = 0
        
        for repo in repositories:
            repo_name = repo['name']
            commits = self.count_commits_for_repo(username, repo_name)
            repo_commits[repo_name] = commits
            total_commits += commits
            if commits > 0:
                active_repos += 1
        
        # Find most active repository
        most_active_repo = None
        most_active_commits = 0
        if repo_commits:
            most_active_repo = max(repo_commits, key=repo_commits.get)
            most_active_commits = repo_commits[most_active_repo]
        
        return {
            'username': username,
            'user_found': True,
            'total_repos': len(repositories),
            'total_commits_past_3_months': total_commits,
            'active_repos': active_repos,
            'avg_commits_per_repo': total_commits / len(repositories) if repositories else 0,
            'most_active_repo': most_active_repo,
            'most_active_repo_commits': most_active_commits,
            'user_type': user_info.get('type', 'Unknown'),
            'public_repos': user_info.get('public_repos', 0),
            'followers': user_info.get('followers', 0),
            'created_at': user_info.get('created_at', 'Unknown'),
            'processed_at': datetime.now().isoformat()
        }
    
    def save_results_batch(self, results: List[Dict], append: bool = True):
        """Save results to CSV file"""
        if not results:
            return
        
        df = pd.DataFrame(results)
        
        if append and os.path.exists(self.results_file):
            # Append to existing file
            df.to_csv(self.results_file, mode='a', header=False, index=False)
        else:
            # Create new file
            df.to_csv(self.results_file, index=False)
        
        print(f"Saved {len(results)} results to {self.results_file}")
    
    def analyze_all_usernames(self, csv_file: str, delay_between_requests: float = 1.0):
        """Analyze all usernames in the CSV file with checkpointing"""
        
        print(f"Loading usernames from {csv_file}...")
        usernames_df = pd.read_csv(csv_file)
        print(f"Loaded {len(usernames_df)} usernames")
        
        # Initialize counters
        total_processed = len(self.processed_usernames)
        batch_results = []
        start_time = time.time()
        
        try:
            for idx, row in usernames_df.iterrows():
                username = row['username']
                
                # Skip if already processed
                if username in self.processed_usernames:
                    continue
                
                print(f"[{idx + 1}/{len(usernames_df)}] Processing {username}...")
                
                # Analyze username activity
                result = self.analyze_username_activity(username)
                
                # Add original CSV data
                result.update({
                    'repository_count': row.get('repository_count', 0),
                    'is_full_time_candidate': row.get('is_full_time_candidate', False)
                })
                
                batch_results.append(result)
                self.processed_usernames.add(username)
                total_processed += 1
                
                # Save checkpoint and results periodically
                if total_processed % self.save_frequency == 0:
                    self.save_checkpoint(self.processed_usernames)
                    self.save_results_batch(batch_results, append=True)
                    batch_results = []
                    
                    # Progress report
                    elapsed_time = time.time() - start_time
                    rate = total_processed / elapsed_time if elapsed_time > 0 else 0
                    remaining = len(usernames_df) - total_processed
                    eta_hours = remaining / rate / 3600 if rate > 0 else 0
                    
                    print(f"Progress: {total_processed}/{len(usernames_df)} usernames processed")
                    print(f"Rate: {rate:.2f} usernames/sec")
                    print(f"ETA: {eta_hours:.1f} hours remaining")
                    print("-" * 50)
                
                # Rate limiting
                time.sleep(delay_between_requests)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user. Saving progress...")
            self.save_checkpoint(self.processed_usernames)
            if batch_results:
                self.save_results_batch(batch_results, append=True)
            print("Progress saved. You can restart the script to continue from where you left off.")
            return
        
        except Exception as e:
            print(f"\nError during analysis: {e}")
            print("Saving progress...")
            self.save_checkpoint(self.processed_usernames)
            if batch_results:
                self.save_results_batch(batch_results, append=True)
            raise
        
        # Save final batch
        if batch_results:
            self.save_results_batch(batch_results, append=True)
        
        # Final checkpoint
        self.save_checkpoint(self.processed_usernames)
        
        print(f"\nAnalysis complete! Processed {total_processed} usernames")
        print(f"Results saved to: {self.results_file}")
        print(f"Checkpoint saved to: {self.checkpoint_file}")
    
    def generate_summary(self):
        """Generate summary from saved results"""
        if not os.path.exists(self.results_file):
            print("No results file found!")
            return
        
        print("Loading results for summary...")
        df = pd.read_csv(self.results_file)
        
        # Filter valid results
        valid_results = df[df['user_found'] == True].copy()
        
        if len(valid_results) == 0:
            print("No valid results found!")
            return
        
        print(f"\nSummary Statistics:")
        print(f"Total usernames analyzed: {len(df)}")
        print(f"Valid users found: {len(valid_results)}")
        print(f"Total commits (past 3 months): {valid_results['total_commits_past_3_months'].sum()}")
        print(f"Average commits per user: {valid_results['total_commits_past_3_months'].mean():.2f}")
        print(f"Median commits per user: {valid_results['total_commits_past_3_months'].median():.2f}")
        print(f"Max commits by a user: {valid_results['total_commits_past_3_months'].max()}")
        
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
        
        valid_results['activity_category'] = valid_results['total_commits_past_3_months'].apply(categorize_activity)
        activity_counts = valid_results['activity_category'].value_counts()
        
        print(f"\nActivity Distribution:")
        for category, count in activity_counts.items():
            percentage = (count / len(valid_results)) * 100
            print(f"  {category}: {count} users ({percentage:.1f}%)")
        
        # Top users
        print(f"\nTop 10 Most Active Users:")
        top_active = valid_results.nlargest(10, 'total_commits_past_3_months')
        for _, row in top_active.iterrows():
            print(f"  {row['username']}: {row['total_commits_past_3_months']} commits ({row['active_repos']} active repos)")


def main():
    """Main function to run the username analysis"""
    
    # Get GitHub token from environment
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    if not GITHUB_TOKEN:
        print("ERROR: Please set your GITHUB_TOKEN environment variable!")
        print("You can get a token from: https://github.com/settings/tokens")
        return
    
    # Configuration
    csv_file = "../data/github_usernames.csv"
    checkpoint_file = "username_analysis_checkpoint.json"
    results_file = "github_username_activity_results.csv"
    delay_between_requests = 1.0  # seconds between requests
    
    # Initialize analyzer
    analyzer = GitHubUsernameActivityAnalyzer(
        github_token=GITHUB_TOKEN,
        checkpoint_file=checkpoint_file,
        results_file=results_file,
        save_frequency=100
    )
    
    # Check if user wants to generate summary only
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        analyzer.generate_summary()
        return
    
    # Run analysis
    print(f"Starting GitHub username activity analysis...")
    print(f"CSV file: {csv_file}")
    print(f"Checkpoint file: {checkpoint_file}")
    print(f"Results file: {results_file}")
    print(f"Delay between requests: {delay_between_requests}s")
    print(f"Save frequency: every {analyzer.save_frequency} usernames")
    
    try:
        analyzer.analyze_all_usernames(csv_file, delay_between_requests)
        
        # Generate summary after completion
        print("\nGenerating final summary...")
        analyzer.generate_summary()
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        print("Check the checkpoint file to resume from where you left off.")


if __name__ == "__main__":
    main() 