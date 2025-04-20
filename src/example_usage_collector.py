import asyncio
from collector import Collector

async def main():
    # You can provide a token directly
    # github_token = "your_github_token_here"
    # collector = Collector(github_token=github_token)
    
    # Or rely on the GITHUB_TOKEN environment variable
    collector = Collector(days=7)  # Uses default 7 days lookback period
    
    # Define a list of repositories to collect data from
    repositories = [
        {
            "username": "geramirez",
            "owner": "geramirez",
            "repo": "test"
        }
    ]
    
    try:
        # Execute the collector to get data from all repositories
        results = await collector.get(repositories)
        
        # Process the results
        print("Data collection completed successfully!")
        print(f"Collected data from {len(results)} repositories")
        
        # Print keys for each repository result
        for repo_id, result in results.items():
            if "error" in result:
                print(f"Error collecting data for {repo_id}: {result['error']}")
            else:
                print(f"Repository {repo_id} data keys: {result.keys()}")
                
        # Further processing of results can be done here
        
    except Exception as e:
        print(f"Error during collection: {e}")

if __name__ == "__main__":
    asyncio.run(main())