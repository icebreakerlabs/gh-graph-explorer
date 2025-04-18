import asyncio
from user_work_fetcher import UserWorkFetcher

async def main():
    # You can provide a token directly or set it as an environment variable
    # github_token = "your_github_token_here"
    # query = UserWorkFetcher(github_token)
    
    # Or use the environment variable GITHUB_TOKEN
    query = UserWorkFetcher()
    
    # Example GitHub username and repository details
    username = "geramirez"  # Replace with actual GitHub username
    owner = "geramirez"      # Repository owner
    repo = "test" # Repository name
    
    # Optional: specify project fields
    add_project_fields = False
    project_field = "Status"  # Example project field name
    
    try:
        # Execute the query with the simplified get method
        result = await query.get(
            username=username,
            owner=owner,
            repo=repo,
            days=30,  # Look back 30 days by default
            add_project_fields=add_project_fields,
            project_field=project_field
        )
        
        # Process the results
        print("Query executed successfully!")
        print(f"Result: {result.keys()}")          
        
        # You can process other parts of the result as needed
        
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    asyncio.run(main())