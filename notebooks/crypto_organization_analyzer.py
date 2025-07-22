#!/usr/bin/env python3
"""
Crypto Organization Analyzer

This script analyzes the first 10 organizations in crypto_organizations.csv,
focusing on their top repositories and most active contributors.
"""

import json
import requests
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
import time
import os
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()

class CryptoOrganizationAnalyzer:
    def __init__(self, github_token: str, max_repos_per_org: int = 20, max_contributors_per_repo: int = 50):
        """Initialize the analyzer"""
        self.github_token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Analysis limits
        self.max_repos_per_org = max_repos_per_org
        self.max_contributors_per_repo = max_contributors_per_repo
        
        # Calculate date range (6 months ago for broader analysis)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=180)
        self.since_date = self.start_date.strftime('%Y-%m-%d')
        
        print(f"Analyzing activity from {self.since_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Limits: {max_repos_per_org} repos/org, {max_contributors_per_repo} contributors/repo")
    
    def get_organization_info(self, org_name: str) -> dict:
        """Get basic organization information"""
        url = f'https://api.github.com/orgs/{org_name}'
        max_retries = 3
        retry_delay = 60  # Wait 60 seconds for rate limits
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403 and 'rate limit' in response.text.lower():
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit for org info {org_name}, waiting {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                elif response.status_code == 404:
                    print(f"Organization {org_name} not found")
                    return None
                else:
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting org info for {org_name}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting org info for {org_name}: {e}")
                    return None
        
        return None
    
    def get_organization_repositories(self, org_name: str) -> List[Dict]:
        """Get top repositories for an organization (sorted by stars)"""
        url = f'https://api.github.com/orgs/{org_name}/repos'
        params = {
            'per_page': 100,
            'sort': 'stars',
            'direction': 'desc'
        }
        
        repositories = []
        max_retries = 3
        retry_delay = 60  # Wait 60 seconds for rate limits
        
        for attempt in range(max_retries):
            try:
                while url and len(repositories) < self.max_repos_per_org:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        repos = response.json()
                        # Only take up to max_repos_per_org
                        remaining = self.max_repos_per_org - len(repositories)
                        repositories.extend(repos[:remaining])
                        
                        # Check for next page
                        if 'next' in response.links and len(repositories) < self.max_repos_per_org:
                            url = response.links['next']['url']
                            params = {}
                        else:
                            url = None
                            
                    elif response.status_code == 403 and 'rate limit' in response.text.lower():
                        if attempt < max_retries - 1:
                            print(f"Rate limit hit for repos {org_name}, waiting {retry_delay}s...")
                            time.sleep(retry_delay)
                            break
                        else:
                            return repositories
                    elif response.status_code == 404:
                        print(f"Organization {org_name} not found")
                        return []
                    else:
                        print(f"Error {response.status_code} for {org_name} repos")
                        return []
                
                return repositories
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting repos for {org_name}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting repos for {org_name}: {e}")
                    return repositories
        
        return repositories
    
    def get_repo_contributors(self, org_name: str, repo_name: str) -> List[Dict]:
        """Get contributors for a specific repository"""
        url = f'https://api.github.com/repos/{org_name}/{repo_name}/contributors'
        params = {
            'per_page': 100
        }
        
        contributors = []
        max_retries = 3
        retry_delay = 60  # Wait 60 seconds for rate limits
        
        for attempt in range(max_retries):
            try:
                while url and len(contributors) < self.max_contributors_per_repo:
                    response = requests.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        contribs = response.json()
                        # Only take up to max_contributors_per_repo
                        remaining = self.max_contributors_per_repo - len(contributors)
                        contributors.extend(contribs[:remaining])
                        
                        # Check for next page
                        if 'next' in response.links and len(contributors) < self.max_contributors_per_repo:
                            url = response.links['next']['url']
                            params = {}
                        else:
                            url = None
                            
                    elif response.status_code == 403 and 'rate limit' in response.text.lower():
                        if attempt < max_retries - 1:
                            print(f"Rate limit hit for contributors {org_name}/{repo_name}, waiting {retry_delay}s...")
                            time.sleep(retry_delay)
                            break
                        else:
                            return contributors
                    elif response.status_code == 404:
                        print(f"Repository {org_name}/{repo_name} not found")
                        return []
                    else:
                        print(f"Error {response.status_code} for {org_name}/{repo_name} contributors")
                        return []
                
                return contributors
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception getting contributors for {org_name}/{repo_name}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception getting contributors for {org_name}/{repo_name}: {e}")
                    return contributors
        
        return contributors
    
    def count_commits_for_repo(self, org_name: str, repo_name: str) -> int:
        """Count commits in a repository since a specific date"""
        url = f'https://api.github.com/repos/{org_name}/{repo_name}/commits'
        params = {
            'since': self.since_date,
            'per_page': 100
        }
        
        total_commits = 0
        max_retries = 3
        retry_delay = 60  # Wait 60 seconds for rate limits
        
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
                            print(f"Rate limit hit for commits {org_name}/{repo_name}, waiting {retry_delay}s...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            return 0  # Access forbidden
                    else:
                        return 0
                
                return total_commits
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Exception for commits {org_name}/{repo_name}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"Final exception for commits {org_name}/{repo_name}: {e}")
                    return 0
        
        return total_commits
    
    def analyze_organization(self, org_name: str) -> dict:
        """Analyze a single organization"""
        print(f"\n{'='*60}")
        print(f"Analyzing organization: {org_name}")
        print(f"{'='*60}")
        
        # Get organization info
        org_info = self.get_organization_info(org_name)
        if not org_info:
            return {
                'organization': org_name,
                'org_found': False,
                'total_repos': 0,
                'top_repos': [],
                'top_contributors': [],
                'total_commits_past_6_months': 0,
                'processed_at': datetime.now().isoformat()
            }
        
        # Get organization repositories
        repositories = self.get_organization_repositories(org_name)
        
        if not repositories:
            return {
                'organization': org_name,
                'org_found': True,
                'total_repos': 0,
                'top_repos': [],
                'top_contributors': [],
                'total_commits_past_6_months': 0,
                'public_repos': org_info.get('public_repos', 0),
                'followers': org_info.get('followers', 0),
                'created_at': org_info.get('created_at', 'Unknown'),
                'processed_at': datetime.now().isoformat()
            }
        
        # Analyze top repositories
        print(f"Analyzing {len(repositories)} top repositories...")
        repo_analysis = []
        all_contributors = {}
        
        for repo in tqdm(repositories, desc=f"Repos for {org_name}"):
            repo_name = repo['name']
            repo_full_name = f"{org_name}/{repo_name}"
            
            # Get repo stats
            commits = self.count_commits_for_repo(org_name, repo_name)
            
            repo_data = {
                'repo_name': repo_name,
                'full_name': repo_full_name,
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'commits_past_6_months': commits,
                'language': repo.get('language', 'Unknown'),
                'created_at': repo.get('created_at', 'Unknown'),
                'updated_at': repo.get('updated_at', 'Unknown'),
                'description': (repo.get('description') or '')[:200]  # Handle None descriptions
            }
            
            repo_analysis.append(repo_data)
            
            # Get contributors for this repo
            contributors = self.get_repo_contributors(org_name, repo_name)
            
            for contrib in contributors:
                username = contrib['login']
                contributions = contrib.get('contributions', 0)
                
                if username not in all_contributors:
                    all_contributors[username] = {
                        'username': username,
                        'total_contributions': 0,
                        'repos_contributed_to': [],
                        'avatar_url': contrib.get('avatar_url', ''),
                        'type': contrib.get('type', 'User')
                    }
                
                all_contributors[username]['total_contributions'] += contributions
                all_contributors[username]['repos_contributed_to'].append(repo_name)
        
        # Sort repositories by commits (most active first)
        repo_analysis.sort(key=lambda x: x['commits_past_6_months'], reverse=True)
        
        # Sort contributors by total contributions
        top_contributors = sorted(
            all_contributors.values(), 
            key=lambda x: x['total_contributions'], 
            reverse=True
        )[:20]  # Top 20 contributors
        
        # Calculate total commits
        total_commits = sum(repo['commits_past_6_months'] for repo in repo_analysis)
        
        return {
            'organization': org_name,
            'org_found': True,
            'total_repos': len(repositories),
            'top_repos': repo_analysis[:10],  # Top 10 repos
            'top_contributors': top_contributors,
            'total_commits_past_6_months': total_commits,
            'public_repos': org_info.get('public_repos', 0),
            'followers': org_info.get('followers', 0),
            'created_at': org_info.get('created_at', 'Unknown'),
            'processed_at': datetime.now().isoformat()
        }
    
    def find_existing_analysis_folders(self) -> List[str]:
        """Find existing analysis folders"""
        import glob
        folders = glob.glob("crypto_analysis_*")
        return sorted(folders, reverse=True)  # Most recent first
    
    def load_existing_results(self, folder_path: str) -> Dict:
        """Load existing results from a folder"""
        try:
            results = {
                'organizations': [],
                'repositories': [],
                'contributors': [],
                'top_contributors': []
            }
            
            # Load organizations summary
            summary_file = os.path.join(folder_path, "organizations_summary.csv")
            if os.path.exists(summary_file):
                df = pd.read_csv(summary_file)
                results['organizations'] = df.to_dict('records')
                print(f"Found existing analysis in {folder_path} with {len(df)} organizations")
            
            # Load repositories
            repo_file = os.path.join(folder_path, "repositories.csv")
            if os.path.exists(repo_file):
                df = pd.read_csv(repo_file)
                results['repositories'] = df.to_dict('records')
                print(f"  - {len(df)} repositories")
            
            # Load contributors
            contrib_file = os.path.join(folder_path, "contributors.csv")
            if os.path.exists(contrib_file):
                df = pd.read_csv(contrib_file)
                results['contributors'] = df.to_dict('records')
                print(f"  - {len(df)} contributors")
            
            # Load top contributors
            top_contrib_file = os.path.join(folder_path, "top_contributors.csv")
            if os.path.exists(top_contrib_file):
                df = pd.read_csv(top_contrib_file)
                results['top_contributors'] = df.to_dict('records')
                print(f"  - {len(df)} top contributors")
            
            return results
        except Exception as e:
            print(f"Error loading existing results from {folder_path}: {e}")
            return {'organizations': [], 'repositories': [], 'contributors': [], 'top_contributors': []}
    
    def analyze_top_organizations(self, num_organizations: int = 100, csv_file: str = "../data/crypto_organizations.csv"):
        """Analyze the top N organizations in the CSV file with resume capability"""
        
        print(f"Loading organizations from {csv_file}...")
        orgs_df = pd.read_csv(csv_file)
        print(f"Loaded {len(orgs_df)} organizations")
        
        # Get top N organizations
        top_orgs = orgs_df.head(num_organizations)
        print(f"Target: Analyze top {num_organizations} organizations")
        
        # Check for existing analysis
        existing_folders = self.find_existing_analysis_folders()
        existing_data = {
            'organizations': [],
            'repositories': [],
            'contributors': [],
            'top_contributors': []
        }
        already_analyzed_orgs = set()
        
        if existing_folders:
            print(f"\n🔍 Checking for existing analysis...")
            for folder in existing_folders[:3]:  # Check last 3 folders
                folder_data = self.load_existing_results(folder)
                if folder_data['organizations']:
                    # Merge data from this folder
                    existing_data['organizations'].extend(folder_data['organizations'])
                    existing_data['repositories'].extend(folder_data['repositories'])
                    existing_data['contributors'].extend(folder_data['contributors'])
                    existing_data['top_contributors'].extend(folder_data['top_contributors'])
                    
                    # Track already analyzed organizations
                    for org in folder_data['organizations']:
                        already_analyzed_orgs.add(org['organization'])
        
        # Remove duplicates from existing data
        if existing_data['organizations']:
            # Remove duplicate organizations (keep most recent)
            seen_orgs = set()
            unique_orgs = []
            for org in reversed(existing_data['organizations']):
                if org['organization'] not in seen_orgs:
                    unique_orgs.append(org)
                    seen_orgs.add(org['organization'])
            existing_data['organizations'] = list(reversed(unique_orgs))
            
            # Remove duplicate repositories (keep most recent)
            seen_repos = set()
            unique_repos = []
            for repo in reversed(existing_data['repositories']):
                repo_key = f"{repo['organization']}/{repo['repo_name']}"
                if repo_key not in seen_repos:
                    unique_repos.append(repo)
                    seen_repos.add(repo_key)
            existing_data['repositories'] = list(reversed(unique_repos))
            
            # Remove duplicate contributors (keep most recent)
            seen_contribs = set()
            unique_contribs = []
            for contrib in reversed(existing_data['contributors']):
                contrib_key = f"{contrib['organization']}/{contrib['username']}"
                if contrib_key not in seen_contribs:
                    unique_contribs.append(contrib)
                    seen_contribs.add(contrib_key)
            existing_data['contributors'] = list(reversed(unique_contribs))
            
            # Remove duplicate top contributors (keep most recent)
            seen_top_contribs = set()
            unique_top_contribs = []
            for contrib in reversed(existing_data['top_contributors']):
                contrib_key = f"{contrib['organization']}/{contrib['username']}"
                if contrib_key not in seen_top_contribs:
                    unique_top_contribs.append(contrib)
                    seen_top_contribs.add(contrib_key)
            existing_data['top_contributors'] = list(reversed(unique_top_contribs))
        
        if already_analyzed_orgs:
            print(f"✅ Already analyzed {len(already_analyzed_orgs)} organizations")
            print(f"📋 Organizations to skip: {', '.join(list(already_analyzed_orgs)[:5])}{'...' if len(already_analyzed_orgs) > 5 else ''}")
        
        # Filter out already analyzed organizations
        remaining_orgs = []
        for idx, row in top_orgs.iterrows():
            org_name = row['organization']
            if org_name not in already_analyzed_orgs:
                remaining_orgs.append((idx, row))
        
        print(f"\n📊 Analysis Plan:")
        print(f"  - Total target: {num_organizations} organizations")
        print(f"  - Already analyzed: {len(already_analyzed_orgs)} organizations")
        print(f"  - Remaining to analyze: {len(remaining_orgs)} organizations")
        
        # Show organizations to be analyzed
        if remaining_orgs:
            print(f"\n📋 Organizations to analyze:")
            for i, (idx, row) in enumerate(remaining_orgs, 1):
                print(f"  {i}. {row['organization']} ({row['repository_count']} repos)")
        
        # Analyze remaining organizations
        new_results = []
        
        for i, (idx, row) in enumerate(remaining_orgs, 1):
            org_name = row['organization']
            
            print(f"\n[{i}/{len(remaining_orgs)}] Analyzing organization: {org_name}")
            
            # Analyze organization
            result = self.analyze_organization(org_name)
            
            # Add original CSV data
            result.update({
                'repository_count': row.get('repository_count', 0),
                'ecosystem_count': row.get('ecosystem_count', 0),
                'avg_repos_per_eco': row.get('avg_repos_per_eco', 0)
            })
            
            new_results.append(result)
            
            # Rate limiting
            if i < len(remaining_orgs):
                time.sleep(2)
        
        # Combine existing and new results
        all_results = []
        
        # Add existing organizations
        for org_data in existing_data['organizations']:
            # Convert CSV data back to result format
            result = {
                'organization': org_data['organization'],
                'org_found': True,
                'total_repos': org_data['total_repos_analyzed'],
                'public_repos': org_data['public_repos'],
                'followers': org_data['followers'],
                'created_at': org_data['created_at'],
                'total_commits_past_6_months': org_data['total_commits_past_6_months'],
                'repository_count': org_data.get('repository_count', 0),
                'ecosystem_count': org_data.get('ecosystem_count', 0),
                'avg_repos_per_eco': org_data.get('avg_repos_per_eco', 0),
                'top_repos': [],
                'top_contributors': [],
                'processed_at': datetime.now().isoformat()
            }
            all_results.append(result)
        
        # Add new results
        all_results.extend(new_results)
        
        return all_results, existing_data
    
    def save_results(self, results: List[Dict], output_file: str = "crypto_organization_analysis.json"):
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {output_file}")
    
    def save_results_to_csv(self, results: List[Dict], existing_data: Dict = None):
        """Save results to multiple CSV files in a timestamped folder"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create output folder
        output_folder = f"crypto_analysis_{timestamp}"
        os.makedirs(output_folder, exist_ok=True)
        print(f"Created output folder: {output_folder}")
        
        # Initialize data lists
        org_summary_data = []
        repo_data = []
        contributor_data = []
        top_contributors_summary = []
        
        # Add existing data if provided
        if existing_data:
            org_summary_data.extend(existing_data['organizations'])
            repo_data.extend(existing_data['repositories'])
            contributor_data.extend(existing_data['contributors'])
            top_contributors_summary.extend(existing_data['top_contributors'])
            print(f"📊 Merged {len(existing_data['organizations'])} existing organizations")
        
        # Add new data from results
        for result in results:
            if result['org_found']:
                # Organization summary
                org_summary_data.append({
                    'organization': result['organization'],
                    'total_repos_analyzed': result['total_repos'],
                    'public_repos': result['public_repos'],
                    'followers': result['followers'],
                    'created_at': result['created_at'],
                    'total_commits_past_6_months': result['total_commits_past_6_months'],
                    'repository_count': result.get('repository_count', 0),
                    'ecosystem_count': result.get('ecosystem_count', 0),
                    'avg_repos_per_eco': result.get('avg_repos_per_eco', 0)
                })
                
                # Repository details
                if result['top_repos']:
                    for repo in result['top_repos']:
                        repo_data.append({
                            'organization': result['organization'],
                            'repo_name': repo['repo_name'],
                            'full_name': repo['full_name'],
                            'stars': repo['stars'],
                            'forks': repo['forks'],
                            'commits_past_6_months': repo['commits_past_6_months'],
                            'language': repo['language'],
                            'created_at': repo['created_at'],
                            'updated_at': repo['updated_at'],
                            'description': repo['description']
                        })
                
                # Contributor details
                if result['top_contributors']:
                    for contrib in result['top_contributors']:
                        contributor_data.append({
                            'organization': result['organization'],
                            'username': contrib['username'],
                            'total_contributions': contrib['total_contributions'],
                            'repos_contributed_to': ', '.join(contrib['repos_contributed_to']),
                            'num_repos_contributed': len(contrib['repos_contributed_to']),
                            'avatar_url': contrib['avatar_url'],
                            'type': contrib['type']
                        })
                
                # Top contributors summary
                if result['top_contributors']:
                    for i, contrib in enumerate(result['top_contributors'][:5], 1):  # Top 5 per org
                        top_contributors_summary.append({
                            'organization': result['organization'],
                            'rank': i,
                            'username': contrib['username'],
                            'total_contributions': contrib['total_contributions'],
                            'num_repos_contributed': len(contrib['repos_contributed_to']),
                            'repos_contributed_to': ', '.join(contrib['repos_contributed_to'][:3])  # First 3 repos
                        })
        
        # Save CSV files
        if org_summary_data:
            org_summary_df = pd.DataFrame(org_summary_data)
            org_summary_file = os.path.join(output_folder, "organizations_summary.csv")
            org_summary_df.to_csv(org_summary_file, index=False)
            print(f"Organization summary saved to: {org_summary_file} ({len(org_summary_data)} organizations)")
        
        if repo_data:
            repo_df = pd.DataFrame(repo_data)
            repo_file = os.path.join(output_folder, "repositories.csv")
            repo_df.to_csv(repo_file, index=False)
            print(f"Repository details saved to: {repo_file} ({len(repo_data)} repositories)")
        
        if contributor_data:
            contributor_df = pd.DataFrame(contributor_data)
            contributor_file = os.path.join(output_folder, "contributors.csv")
            contributor_df.to_csv(contributor_file, index=False)
            print(f"Contributor details saved to: {contributor_file} ({len(contributor_data)} contributors)")
        
        if top_contributors_summary:
            top_contrib_df = pd.DataFrame(top_contributors_summary)
            top_contrib_file = os.path.join(output_folder, "top_contributors.csv")
            top_contrib_df.to_csv(top_contrib_file, index=False)
            print(f"Top contributors summary saved to: {top_contrib_file} ({len(top_contributors_summary)} entries)")
        
        # Analysis Summary CSV
        analysis_summary = {
            'analysis_date': timestamp,
            'organizations_analyzed': len(org_summary_data),
            'total_repositories_analyzed': len(repo_data),
            'total_contributors_found': len(contributor_data),
            'total_commits_6_months': sum(org['total_commits_past_6_months'] for org in org_summary_data),
            'analysis_duration_minutes': 'N/A'  # Could be calculated if we track start time
        }
        
        analysis_summary_df = pd.DataFrame([analysis_summary])
        analysis_summary_file = os.path.join(output_folder, "analysis_summary.csv")
        analysis_summary_df.to_csv(analysis_summary_file, index=False)
        print(f"Analysis summary saved to: {analysis_summary_file}")
        
        return {
            'output_folder': output_folder,
            'org_summary': org_summary_file if org_summary_data else None,
            'repositories': repo_file if repo_data else None,
            'contributors': contributor_file if contributor_data else None,
            'top_contributors': top_contrib_file if top_contributors_summary else None,
            'analysis_summary': analysis_summary_file
        }
    
    def print_summary(self, results: List[Dict]):
        """Print a summary of the analysis"""
        print(f"\n{'='*80}")
        print("CRYPTO ORGANIZATION ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        for result in results:
            org_name = result['organization']
            org_found = result['org_found']
            
            if not org_found:
                print(f"\n❌ {org_name}: Organization not found")
                continue
            
            print(f"\n🏢 {org_name}")
            print(f"   📊 Total repos analyzed: {result['total_repos']}")
            print(f"   ⭐ Public repos: {result['public_repos']}")
            print(f"   👥 Followers: {result['followers']}")
            print(f"   📅 Created: {result['created_at'][:10]}")
            print(f"   🔥 Total commits (6 months): {result['total_commits_past_6_months']}")
            
            # Top repositories
            if result['top_repos']:
                print(f"   📈 Top 5 repositories by activity:")
                for i, repo in enumerate(result['top_repos'][:5], 1):
                    print(f"      {i}. {repo['repo_name']}: {repo['commits_past_6_months']} commits, {repo['stars']} stars")
            
            # Top contributors
            if result['top_contributors']:
                print(f"   👨‍💻 Top 5 contributors:")
                for i, contrib in enumerate(result['top_contributors'][:5], 1):
                    print(f"      {i}. {contrib['username']}: {contrib['total_contributions']} contributions ({len(contrib['repos_contributed_to'])} repos)")


def main():
    """Main function to run the analysis"""
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description='Analyze crypto organizations from CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crypto_organization_analyzer.py --num-orgs 10          # Analyze top 10 organizations
  python crypto_organization_analyzer.py --num-orgs 50          # Analyze top 50 organizations  
  python crypto_organization_analyzer.py --num-orgs 100         # Analyze top 100 organizations
  python crypto_organization_analyzer.py --num-orgs 10 --csv-file data/custom_orgs.csv
        """
    )
    
    parser.add_argument(
        '--num-orgs', 
        type=int, 
        default=100,
        help='Number of top organizations to analyze (default: 100)'
    )
    
    parser.add_argument(
        '--csv-file',
        type=str,
        default='../data/crypto_organizations.csv',
        help='Path to CSV file containing organizations (default: ../data/crypto_organizations.csv)'
    )
    
    parser.add_argument(
        '--max-repos',
        type=int,
        default=20,
        help='Maximum repositories to analyze per organization (default: 20)'
    )
    
    parser.add_argument(
        '--max-contributors',
        type=int,
        default=50,
        help='Maximum contributors to analyze per repository (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.num_orgs <= 0:
        print("ERROR: --num-orgs must be greater than 0")
        return
    
    if args.max_repos <= 0:
        print("ERROR: --max-repos must be greater than 0")
        return
    
    if args.max_contributors <= 0:
        print("ERROR: --max-contributors must be greater than 0")
        return
    
    # Get GitHub token from environment
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    if not GITHUB_TOKEN:
        print("ERROR: Please set your GITHUB_TOKEN environment variable!")
        print("You can get a token from: https://github.com/settings/tokens")
        return
    
    # Initialize analyzer
    analyzer = CryptoOrganizationAnalyzer(
        github_token=GITHUB_TOKEN,
        max_repos_per_org=args.max_repos,
        max_contributors_per_repo=args.max_contributors
    )
    
    # Run analysis
    print(f"Starting crypto organization analysis...")
    print(f"Configuration:")
    print(f"  - Organizations to analyze: {args.num_orgs}")
    print(f"  - CSV file: {args.csv_file}")
    print(f"  - Max repos per org: {args.max_repos}")
    print(f"  - Max contributors per repo: {args.max_contributors}")
    
    results, existing_data = analyzer.analyze_top_organizations(
        num_organizations=args.num_orgs,
        csv_file=args.csv_file
    )
    
    if not results and not existing_data['organizations']:
        print("\n🎉 No organizations to analyze!")
        print("No target organizations found.")
        return
    
    # Save results
    if results:
        analyzer.save_results(results)
    
    # Save to CSV files (including existing data)
    csv_files = analyzer.save_results_to_csv(results, existing_data)
    
    # Print summary
    if results:
        analyzer.print_summary(results)
    
    total_orgs = len(existing_data['organizations']) + len(results)
    new_orgs = len(results)
    
    print(f"\nAnalysis complete!")
    if new_orgs > 0:
        print(f"  - Analyzed {new_orgs} new organizations")
    if existing_data['organizations']:
        print(f"  - Included {len(existing_data['organizations'])} existing organizations")
    print(f"  - Total organizations in results: {total_orgs}")
    
    print(f"\n📁 All results saved to folder: {csv_files['output_folder']}")
    print(f"📊 CSV files created:")
    for file_type, filename in csv_files.items():
        if filename and file_type != 'output_folder':
            print(f"  - {file_type}: {filename}")


if __name__ == "__main__":
    main() 