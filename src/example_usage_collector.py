import asyncio
import os
from collector import Collector
from save_strategy import PrintSave, CSVSave


async def main():
    # Example repositories to collect data from
    repos = [
        {
            "username": "geramirez",
            "owner": "geramirez", 
            "repo": "test"
        }
    ]
    
    # Get GitHub token from environment (if available)
    github_token = os.environ.get("GITHUB_TOKEN")
    
    print("Example 1: Using PrintSave strategy (default)")
    print("-" * 50)
    # Create collector with default PrintSave strategy
    collector = Collector(days=30, github_token=github_token, save_strategy=PrintSave())
    results = await collector.get(repos)
    print(f"Results: {results}\n")
    
    print("Example 2: Using CSVSave strategy with default filename")
    print("-" * 50)
    # Create collector with CSVSave strategy and default filename
    csv_save = CSVSave()
    collector = Collector(days=30, github_token=github_token, save_strategy=csv_save)
    results = await collector.get(repos)
    print(f"Results: {results}")
    print(f"Edges saved to: {csv_save.filename}\n")
    
    print("Example 3: Using CSVSave strategy with custom filename")
    print("-" * 50)
    # Create collector with CSVSave strategy and custom filename
    custom_filename = "custom_github_edges.csv"
    csv_save = CSVSave(filename=custom_filename)
    collector = Collector(days=30, github_token=github_token, save_strategy=csv_save)
    results = await collector.get(repos)
    print(f"Results: {results}")
    print(f"Edges saved to: {custom_filename}")


if __name__ == "__main__":
    asyncio.run(main())