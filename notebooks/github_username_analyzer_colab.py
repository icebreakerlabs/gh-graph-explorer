#!/usr/bin/env python3
"""
GitHub Username Activity Analyzer for Google Colab

This script analyzes GitHub activity for a slice of usernames from the CSV file.
Designed to be run in Google Colab with different slice parameters for parallel processing.
"""

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
from typing import List, Dict, Optional
from google.colab import files
import io
from tqdm.notebook import tqdm

class ColabGitHubUsernameAnalyzer:
    def __init__(self, github_token: str, slice_start: int = 0, slice_end: int = None, 
                 slice_id: str = "slice1", save_frequency: int = 50,
                 max_repos_per_user: int = 50, max_commits_per_repo: int = 1000):
        """Initialize the analyzer for a specific slice"""
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Slice configuration
        self.slice_start = slice_start
        self.slice_end = slice_end
        self.slice_id = slice_id
        
        # Performance optimization limits
        self.max_repos_per_user = max_repos_per_user
        self.max_commits_per_repo = max_commits_per_repo
        
        # Calculate date range (3 months ago)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=90)
        self.since_date = self.start_date.strftime('%Y-%m-%d')
        
        # File management
        self.results_file = f"github_username_activity_results_{slice_id}.csv"
        self.checkpoint_file = f"username_analysis_checkpoint_{slice_id}.json"
        self.save_frequency = save_frequency
        
        # Load checkpoint if exists
        self.processed_usernames = self.load_checkpoint()
        
        print(f"Slice {slice_id}: Analyzing usernames {slice_start} to {slice_end}")
        print(f"Analyzing commits from {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Performance limits: {max_repos_per_user} repos/user, {max_commits_per_repo} commits/repo")
        print(f"Already processed: {len(self.processed_usernames)} usernames in this slice")
        print(f"Results file: {self.results_file}")
        print(f"Checkpoint file: {self.checkpoint_file}")
    
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
            'total_processed': len(processed_usernames),
            'slice_id': self.slice_id,
            'slice_start': self.slice_start,
            'slice_end': self.slice_end
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
    
    def get_user_repositories(self, username: str, max_repos: int = 50) -> List[Dict]:
        """Get repositories for a user (limited to most recent)"""
        url = f'https://api.github.com/users/{username}/repos'
        params = {
            'per_page': min(100, max_repos),  # Limit to max_repos
            'sort': 'updated',
            'direction': 'desc'
        }
        
        repositories = []
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                while url and len(repositories) < max_repos:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        repos = response.json()
                        # Only take up to max_repos
                        remaining = max_repos - len(repositories)
                        repositories.extend(repos[:remaining])
                        
                        # Check for next page
                        if 'next' in response.links and len(repositories) < max_repos:
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
    
    def count_commits_for_repo(self, owner: str, repo: str, max_commits: int = 1000) -> int:
        """Count commits in a repository since a specific date (with limit)"""
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
                while url and total_commits < max_commits:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        commits = response.json()
                        # Limit commits to max_commits
                        remaining = max_commits - total_commits
                        commit_count = min(len(commits), remaining)
                        total_commits += commit_count
                        
                        # If we hit the limit, stop
                        if total_commits >= max_commits:
                            break
                        
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
    
    def analyze_username_activity(self, username: str, max_repos_per_user: int = 50, max_commits_per_repo: int = 1000) -> dict:
        """Analyze activity for a single username (optimized)"""
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
                'user_type': 'Unknown',
                'public_repos': 0,
                'followers': 0,
                'created_at': 'Unknown',
                'processed_at': datetime.now().isoformat()
            }
        
        # Get user repositories (limited)
        repositories = self.get_user_repositories(username, max_repos=max_repos_per_user)
        
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
        
        # Analyze commits for each repository (with early termination)
        repo_commits = {}
        total_commits = 0
        active_repos = 0
        
        for repo in tqdm(repositories, desc=f"Repos for {username}", leave=False):
            repo_name = repo['name']
            commits = self.count_commits_for_repo(username, repo_name, max_commits_per_repo)
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
    
    def download_results(self):
        """Download results file from Colab"""
        if os.path.exists(self.results_file):
            files.download(self.results_file)
            print(f"Downloaded {self.results_file}")
        else:
            print("No results file to download")
    
    def analyze_slice(self, csv_data: str, delay_between_requests: float = 1.0):
        """Analyze a slice of usernames from CSV data"""
        
        print(f"Loading usernames from CSV data...")
        usernames_df = pd.read_csv(io.StringIO(csv_data))
        print(f"Loaded {len(usernames_df)} total usernames")
        
        # Apply slice
        if self.slice_end is None:
            self.slice_end = len(usernames_df)
        
        slice_df = usernames_df.iloc[self.slice_start:self.slice_end].copy()
        print(f"Processing slice: usernames {self.slice_start} to {self.slice_end} ({len(slice_df)} usernames)")
        
        # Initialize counters
        total_processed = len(self.processed_usernames)
        batch_results = []
        start_time = time.time()
        
        try:
            for idx, row in tqdm(slice_df.iterrows(), total=len(slice_df), desc=f"Usernames {self.slice_start}-{self.slice_end}"):
                username = row['username']
                
                # Skip if already processed
                if username in self.processed_usernames:
                    continue
                
                print(f"[{idx + 1}/{len(slice_df)}] Processing {username}...")
                
                # Analyze username activity
                result = self.analyze_username_activity(username,
                                                         max_repos_per_user=self.max_repos_per_user,
                                                         max_commits_per_repo=self.max_commits_per_repo)
                
                # Add original CSV data
                result.update({
                    'repository_count': row.get('repository_count', 0),
                    'is_full_time_candidate': row.get('is_full_time_candidate', False),
                    'slice_id': self.slice_id,
                    'slice_start': self.slice_start,
                    'slice_end': self.slice_end
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
                    remaining = len(slice_df) - total_processed
                    eta_hours = remaining / rate / 3600 if rate > 0 else 0
                    
                    print(f"Progress: {total_processed}/{len(slice_df)} usernames processed")
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
        
        print(f"\nAnalysis complete! Processed {total_processed} usernames in slice {self.slice_id}")
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
        
        print(f"\nSummary Statistics for Slice {self.slice_id}:")
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
        print(f"\nTop 10 Most Active Users in Slice:")
        top_active = valid_results.nlargest(10, 'total_commits_past_3_months')
        for _, row in top_active.iterrows():
            print(f"  {row['username']}: {row['total_commits_past_3_months']} commits ({row['active_repos']} active repos)")


# ============================================================================
# COLAB NOTEBOOK CELLS (Copy these into separate cells in Colab)
# ============================================================================

"""
# CELL 1: Install dependencies and setup
!pip install requests pandas numpy

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
from typing import List, Dict, Optional
from google.colab import files
import io

print("Dependencies installed and imported!")
"""

"""
# CELL 2: Upload CSV file
print("Please upload your github_usernames.csv file:")
uploaded = files.upload()

# Read the uploaded file
csv_filename = list(uploaded.keys())[0]
csv_content = uploaded[csv_filename].decode('utf-8')

print(f"Uploaded file: {csv_filename}")
print(f"File size: {len(csv_content)} characters")
"""

"""
# CELL 3: Configure your slice parameters
# Modify these values for each notebook

GITHUB_TOKEN = "your_github_token_here"  # Replace with your token
SLICE_ID = "slice1"  # Change for each notebook: slice1, slice2, slice3
SLICE_START = 0  # Starting index (0-based)
SLICE_END = 41775  # Ending index (exclusive)

# Performance optimization settings (adjust these for speed vs accuracy)
MAX_REPOS_PER_USER = 20  # Limit repos per user (default: 50, faster: 20)
MAX_COMMITS_PER_REPO = 500  # Limit commits per repo (default: 1000, faster: 500)

# For 3 notebooks, use these ranges:
# Notebook 1: SLICE_START = 0, SLICE_END = 41775 (first 1/3)
# Notebook 2: SLICE_START = 41775, SLICE_END = 83550 (second 1/3)  
# Notebook 3: SLICE_START = 83550, SLICE_END = None (last 1/3)

print(f"Slice Configuration:")
print(f"Slice ID: {SLICE_ID}")
print(f"Range: {SLICE_START} to {SLICE_END}")
print(f"Performance: {MAX_REPOS_PER_USER} repos/user, {MAX_COMMITS_PER_REPO} commits/repo")
"""

"""
# CELL 4: Initialize analyzer and run analysis
# Initialize the analyzer
analyzer = ColabGitHubUsernameAnalyzer(
    github_token=GITHUB_TOKEN,
    slice_start=SLICE_START,
    slice_end=SLICE_END,
    slice_id=SLICE_ID,
    save_frequency=50,
    max_repos_per_user=MAX_REPOS_PER_USER,
    max_commits_per_repo=MAX_COMMITS_PER_REPO
)

# Run the analysis
analyzer.analyze_slice(csv_content, delay_between_requests=1.0)

# Generate summary
analyzer.generate_summary()

# Download results
analyzer.download_results()
"""

"""
# CELL 5: Resume analysis (if interrupted)
# If you need to resume from where you left off, run this cell:

analyzer = ColabGitHubUsernameAnalyzer(
    github_token=GITHUB_TOKEN,
    slice_start=SLICE_START,
    slice_end=SLICE_END,
    slice_id=SLICE_ID,
    save_frequency=50,
    max_repos_per_user=MAX_REPOS_PER_USER,
    max_commits_per_repo=MAX_COMMITS_PER_REPO
)

# Generate summary of current progress
analyzer.generate_summary()

# Continue analysis
analyzer.analyze_slice(csv_content, delay_between_requests=1.0)
"""

"""
# CELL 6: Download all results
# Download the results file
analyzer.download_results()

# Also download checkpoint file for backup
if os.path.exists(analyzer.checkpoint_file):
    files.download(analyzer.checkpoint_file)
    print(f"Downloaded checkpoint: {analyzer.checkpoint_file}")
""" 