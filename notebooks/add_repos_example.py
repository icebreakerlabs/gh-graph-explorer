#!/usr/bin/env python3
"""
Example: How to Add Specific Repositories to Crypto Analysis

This script shows different ways to add repositories to your analysis:
1. Add specific repositories to crypto analysis
2. Create a custom repository list
3. Analyze specific repositories directly
"""

import os
import sys
sys.path.append('.')

from crypto_repo_analyzer import CryptoRepoAnalyzer

def example_add_specific_repos():
    """Example: Add specific repositories to the crypto analysis"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return
    
    # Define repositories you want to add
    manual_repos = [
        {
            "owner": "ethereum",
            "repo": "go-ethereum",
            "ecosystem": "ethereum"
        },
        {
            "owner": "bitcoin",
            "repo": "bitcoin",
            "ecosystem": "bitcoin"
        },
        {
            "owner": "solana-labs",
            "repo": "solana",
            "ecosystem": "solana"
        },
        {
            "owner": "chainlink",
            "repo": "chainlink",
            "ecosystem": "oracle"
        }
    ]
    
    print("🎯 Adding Specific Repositories to Crypto Analysis")
    print("=" * 50)
    
    analyzer = CryptoRepoAnalyzer(github_token)
    
    # Run analysis with manual repositories included
    # This will add your manual repos + select others automatically
    results = analyzer.run_full_analysis(
        months_back=6,
        target_repo_count=15,  # Total repos including manual ones
        manual_repos=manual_repos
    )
    
    print("\n✅ Analysis complete with your custom repositories!")

def example_create_custom_config():
    """Example: Create a custom configuration file for specific repositories"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return
    
    # Define your custom repository list
    custom_repos = [
        {"owner": "uniswap", "repo": "v3-core", "ecosystem": "defi"},
        {"owner": "aave", "repo": "aave-v3-core", "ecosystem": "defi"},
        {"owner": "compound-finance", "repo": "compound-protocol", "ecosystem": "defi"},
        {"owner": "makerdao", "repo": "dss", "ecosystem": "defi"},
        {"owner": "opensea", "repo": "opensea-js", "ecosystem": "nft"},
    ]
    
    print("⚙️ Creating Custom Repository Configuration")
    print("=" * 50)
    
    analyzer = CryptoRepoAnalyzer(github_token)
    
    # Create configuration for your custom repos
    config_path, summary_path = analyzer.create_multi_repo_config(custom_repos)
    
    print(f"\n📁 Configuration created:")
    print(f"   Config: {config_path}")
    print(f"   Summary: {summary_path}")
    print(f"\n💡 You can now use this config file with the main analysis tool:")
    print(f"   uv run main.py collect --repos {config_path} --output csv")

def example_analyze_specific_repos_only():
    """Example: Analyze only specific repositories (no automatic selection)"""
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        return
    
    # Define only the repositories you want to analyze
    specific_repos = [
        {"owner": "your-org", "repo": "your-repo", "ecosystem": "your-ecosystem"},
        {"owner": "another-org", "repo": "another-repo", "ecosystem": "another-ecosystem"},
    ]
    
    print("🎯 Analyzing Only Specific Repositories")
    print("=" * 50)
    
    analyzer = CryptoRepoAnalyzer(github_token)
    
    # Run analysis with only your specific repos (set target_repo_count to match)
    results = analyzer.run_full_analysis(
        months_back=6,
        target_repo_count=len(specific_repos),  # Only analyze these repos
        manual_repos=specific_repos
    )
    
    print("\n✅ Analysis complete for your specific repositories!")

if __name__ == "__main__":
    print("🚀 Repository Addition Examples")
    print("=" * 50)
    print("Choose an example to run:")
    print("1. Add specific repos to crypto analysis")
    print("2. Create custom configuration")
    print("3. Analyze only specific repositories")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        example_add_specific_repos()
    elif choice == "2":
        example_create_custom_config()
    elif choice == "3":
        example_analyze_specific_repos_only()
    else:
        print("❌ Invalid choice. Running example 1...")
        example_add_specific_repos() 