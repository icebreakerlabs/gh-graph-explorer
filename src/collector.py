import asyncio
from typing import List, Dict, Any, Optional
from user_work_fetcher import UserWorkFetcher
from edge_factory import EdgeFactory

class Collector:
    """
    Class to collect GitHub work data from multiple repositories for a user.
    """
    def __init__(self, days: int = 7, github_token: Optional[str] = None):
        """
        Initialize the Collector with the number of days to look back.
        
        Args:
            days: Number of days to look back for GitHub activity (default: 7)
            github_token: GitHub personal access token with appropriate permissions.
                          If None, will try to use GITHUB_TOKEN from environment variables.
        """
        self.days = days
        self.fetcher = UserWorkFetcher()
    
    async def get(self, repos: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Collect GitHub work data from multiple repositories.
        
        Args:
            repos: List of dictionaries, each containing 'username', 'owner', and 'repo' keys
            
        Returns:
            Dictionary with repository identifiers as keys and fetched data as values
        """
        if not repos:
            raise ValueError("No repositories provided")
            
        results = {}
        
        # Process each repository
        for repo_info in repos:
            # Validate required keys
            required_keys = ['username', 'owner', 'repo']
            if not all(key in repo_info for key in required_keys):
                missing = [key for key in required_keys if key not in repo_info]
                raise ValueError(f"Missing required keys in repository info: {missing}")
            
            # Create a unique identifier for this repository
            repo_id = f"{repo_info['owner']}/{repo_info['repo']}"
            
            # Fetch data for this repository
            try:
                result = await self.fetcher.get(
                    username=repo_info['username'],
                    owner=repo_info['owner'],
                    repo=repo_info['repo'],
                    days=self.days
                )

                for edge in EdgeFactory(result).generate_edges():
                    print(edge)

            except Exception as e:
                # Store the error for this repository but continue with others
                results[repo_id] = {"error": str(e)}
        
        return results