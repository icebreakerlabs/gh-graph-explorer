#!/usr/bin/env python3
"""
Full GitHub Repository Activity Analyzer

This script analyzes ALL repositories in the JSONL file with checkpointing
to resume from where it left off if interrupted.
"""

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
import os
import sys
from typing import List, Dict, Optional, Tuple
import dotenv

dotenv.load_dotenv()

class FullRepoActivityAnalyzer:
    def __init__(self, github_token: str, checkpoint_file: str = "checkpoint.json", 
                 results_file: str = "full_repo_activity_results.csv",
                 batch_size: int = 1000, save_frequency: int = 100):
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
        self.batch_size = batch_size
        self.save_frequency = save_frequency
        
        # Load checkpoint if exists
        self.processed_repos = self.load_checkpoint()
        
        print(f"Analyzing commits from {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Already processed: {len(self.processed_repos)} repositories")
        print(f"Checkpoint file: {checkpoint_file}")
        print(f"Results file: {results_file}")
    
    def load_checkpoint(self) -> set:
        """Load processed repositories from checkpoint file"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                    return set(checkpoint_data.get('processed_repos', []))
            except Exception as e:
                print(f"Error loading checkpoint: {e}")
        return set()
    
    def save_checkpoint(self, processed_repos: set):
        """Save checkpoint with processed repositories"""
        checkpoint_data = {
            'processed_repos': list(processed_repos),
            'last_updated': datetime.now().isoformat(),
            'total_processed': len(processed_repos)
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
    
    def load_jsonl_as_generator(self, file_path: str):
        """Load JSONL file as a generator to handle large files efficiently"""
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        yield json.loads(line.strip()), line_num
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line {line_num}: {e}")
                        continue
    
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
        """Count commits in a repository since a specific date with retry logic"""
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
                        print(f"Repository {owner}/{repo} not found")
                        return -1
                    elif response.status_code == 403:
                        if 'rate limit' in response.text.lower():
                            wait_time = retry_delay * (2 ** attempt)
                            print(f"Rate limit hit for {owner}/{repo}, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"Access forbidden for {owner}/{repo}")
                            return -2
                    elif response.status_code == 401:
                        print(f"Unauthorized for {owner}/{repo}")
                        return -3
                    else:
                        print(f"Error {response.status_code} for {owner}/{repo}")
                        return -4
                
                return total_commits
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception for {owner}/{repo}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception for {owner}/{repo}: {e}")
                    return -5
        
        return total_commits
    
    def get_repo_info(self, owner: str, repo: str) -> dict:
        """Get basic repository information with retry logic"""
        url = f'https://api.github.com/repos/{owner}/{repo}'
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
                        print(f"Rate limit hit for repo info {owner}/{repo}, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                else:
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting repo info for {owner}/{repo}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting repo info for {owner}/{repo}: {e}")
                    return None
        
        return None
    
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
    
    def analyze_all_repositories(self, jsonl_file: str, delay_between_requests: float = 2.0):
        """Analyze all repositories in the JSONL file with checkpointing"""
        
        print(f"Starting analysis of all repositories in {jsonl_file}")
        print(f"Delay between requests: {delay_between_requests}s")
        
        # Initialize counters
        total_processed = len(self.processed_repos)
        batch_results = []
        start_time = time.time()
        
        try:
            for repo_data, line_num in self.load_jsonl_as_generator(jsonl_file):
                # Skip if already processed
                repo_url = repo_data.get('repo_url', '')
                if repo_url in self.processed_repos:
                    continue
                
                # Check if it's a GitHub repository
                if 'github.com' not in repo_url:
                    continue
                
                # Extract GitHub info
                owner, repo = self.extract_github_info(repo_url)
                if not owner or not repo:
                    continue
                
                # Create unique identifier
                repo_id = f"{owner}/{repo}"
                
                print(f"[{line_num}] Analyzing {repo_id} ({repo_data.get('eco_name', 'Unknown')})...")
                
                # Get repo info
                repo_info = self.get_repo_info(owner, repo)
                
                # Count commits
                commit_count = self.count_commits_since_date(owner, repo)
                
                result = {
                    'owner': owner,
                    'repo': repo,
                    'eco_name': repo_data.get('eco_name', 'Unknown'),
                    'repo_url': repo_url,
                    'commits_past_3_months': commit_count,
                    'stars': repo_info.get('stargazers_count', 0) if repo_info else 0,
                    'forks': repo_info.get('forks_count', 0) if repo_info else 0,
                    'language': repo_info.get('language', 'Unknown') if repo_info else 'Unknown',
                    'created_at': repo_info.get('created_at', 'Unknown') if repo_info else 'Unknown',
                    'updated_at': repo_info.get('updated_at', 'Unknown') if repo_info else 'Unknown',
                    'processed_at': datetime.now().isoformat()
                }
                
                batch_results.append(result)
                self.processed_repos.add(repo_url)
                total_processed += 1
                
                # Save checkpoint and results periodically
                if total_processed % self.save_frequency == 0:
                    self.save_checkpoint(self.processed_repos)
                    self.save_results_batch(batch_results, append=True)
                    batch_results = []
                    
                    # Progress report
                    elapsed_time = time.time() - start_time
                    rate = total_processed / elapsed_time if elapsed_time > 0 else 0
                    print(f"Progress: {total_processed} repos processed, {rate:.2f} repos/sec")
                
                # Rate limiting
                time.sleep(delay_between_requests)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user. Saving progress...")
            self.save_checkpoint(self.processed_repos)
            if batch_results:
                self.save_results_batch(batch_results, append=True)
            print("Progress saved. You can restart the script to continue from where you left off.")
            return
        
        except Exception as e:
            print(f"\nError during analysis: {e}")
            print("Saving progress...")
            self.save_checkpoint(self.processed_repos)
            if batch_results:
                self.save_results_batch(batch_results, append=True)
            raise
        
        # Save final batch
        if batch_results:
            self.save_results_batch(batch_results, append=True)
        
        # Final checkpoint
        self.save_checkpoint(self.processed_repos)
        
        print(f"\nAnalysis complete! Processed {total_processed} repositories")
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
        valid_results = df[df['commits_past_3_months'] >= 0].copy()
        
        if len(valid_results) == 0:
            print("No valid results found!")
            return
        
        print(f"\nSummary Statistics:")
        print(f"Total repositories analyzed: {len(df)}")
        print(f"Valid results: {len(valid_results)}")
        print(f"Total commits (past 3 months): {valid_results['commits_past_3_months'].sum()}")
        print(f"Average commits per repo: {valid_results['commits_past_3_months'].mean():.2f}")
        print(f"Median commits per repo: {valid_results['commits_past_3_months'].median():.2f}")
        print(f"Max commits in a repo: {valid_results['commits_past_3_months'].max()}")
        
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
        
        print(f"\nActivity Distribution:")
        for category, count in activity_counts.items():
            percentage = (count / len(valid_results)) * 100
            print(f"  {category}: {count} repos ({percentage:.1f}%)")
        
        # Top ecosystems
        eco_stats = valid_results.groupby('eco_name')['commits_past_3_months'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        
        print(f"\nTop 10 Most Active Ecosystems:")
        for eco_name, stats in eco_stats.head(10).iterrows():
            print(f"  {eco_name}: {stats['mean']:.2f} avg commits ({stats['count']} repos)")
        
        # Top repositories
        print(f"\nTop 10 Most Active Repositories:")
        top_active = valid_results.nlargest(10, 'commits_past_3_months')
        for _, row in top_active.iterrows():
            print(f"  {row['owner']}/{row['repo']}: {row['commits_past_3_months']} commits ({row['eco_name']})")


def main():
    """Main function to run the full analysis"""
    
    # Get GitHub token from environment
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    if not GITHUB_TOKEN:
        print("ERROR: Please set your GITHUB_TOKEN environment variable!")
        print("You can get a token from: https://github.com/settings/tokens")
        return
    
    # Configuration
    jsonl_file = "../data/exports.jsonl"
    checkpoint_file = "full_analysis_checkpoint.json"
    results_file = "full_repo_activity_results.csv"
    delay_between_requests = 2.0  # seconds between requests
    
    # Initialize analyzer
    analyzer = FullRepoActivityAnalyzer(
        github_token=GITHUB_TOKEN,
        checkpoint_file=checkpoint_file,
        results_file=results_file,
        batch_size=1000,
        save_frequency=100
    )
    
    # Check if user wants to generate summary only
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        analyzer.generate_summary()
        return
    
    # Run analysis
    print(f"Starting full repository analysis...")
    print(f"JSONL file: {jsonl_file}")
    print(f"Checkpoint file: {checkpoint_file}")
    print(f"Results file: {results_file}")
    print(f"Delay between requests: {delay_between_requests}s")
    print(f"Save frequency: every {analyzer.save_frequency} repositories")
    
    try:
        analyzer.analyze_all_repositories(jsonl_file, delay_between_requests)
        
        # Generate summary after completion
        print("\nGenerating final summary...")
        analyzer.generate_summary()
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        print("Check the checkpoint file to resume from where you left off.")


if __name__ == "__main__":
    main() 