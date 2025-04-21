import os
import asyncio
import argparse
from typing import List, Dict
import json
from src.collector import Collector
from src.save_strategies import PrintSave, CSVSave, Neo4jSave
from src.graph_analyzer import GraphAnalyzer
from src.csv_loader import CSVLoader
from src.neo4j_loader import Neo4jLoader

def parse_arguments():
    """
    Parse command line arguments for the GitHub graph explorer
    """
    parser = argparse.ArgumentParser(description='GitHub Work Graph Explorer')
    
    # Add mode subcommands
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Collection mode parser
    collect_parser = subparsers.add_parser('collect', help='Collect GitHub data')
    collect_parser.add_argument('--days', type=int, default=7,
                        help='Number of days to look back (default: 7)')
    collect_parser.add_argument('--repos', type=str, required=True,
                        help='JSON string or file path with repositories information')
    collect_parser.add_argument('--output', type=str, choices=['print', 'csv', 'neo4j'], default='print',
                        help='Output strategy (print, csv, neo4j). Default: print')
    collect_parser.add_argument('--output-file', type=str,
                        help='Output file path for CSV strategy')
    collect_parser.add_argument('--neo4j-uri', type=str, default='bolt://neo4j:7687',
                        help='Neo4j URI (default: bolt://neo4j:7687)')
    collect_parser.add_argument('--neo4j-user', type=str, default='neo4j',
                        help='Neo4j username (default: neo4j)')
    collect_parser.add_argument('--neo4j-password', type=str, default=os.environ.get('NEO4J_PASSWORD', 'password'),
                        help='Neo4j password (default from NEO4J_PASSWORD env var, or "password")')
    
    # Analysis mode parser
    analyze_parser = subparsers.add_parser('analyze', help='Analyze GitHub data graph')
    analyze_parser.add_argument('--source', type=str, choices=['csv', 'neo4j'], required=True,
                        help='Data source for analysis (csv or neo4j)')
    analyze_parser.add_argument('--file', type=str, 
                        help='CSV file path for analysis when source is csv')
    analyze_parser.add_argument('--neo4j-uri', type=str, default='bolt://neo4j:7687',
                        help='Neo4j URI (default: bolt://neo4j:7687)')
    analyze_parser.add_argument('--neo4j-user', type=str, default='neo4j',
                        help='Neo4j username (default: neo4j)')
    analyze_parser.add_argument('--neo4j-password', type=str, default=os.environ.get('NEO4J_PASSWORD', 'password'),
                        help='Neo4j password (default from NEO4J_PASSWORD env var, or "password")')
    analyze_parser.add_argument('--neo4j-query', type=str,
                        help='Custom Neo4j query for analysis')
                        
    return parser.parse_args()

def parse_repos_config(repos_config: str) -> List[Dict[str, str]]:
    """
    Parse the repositories configuration from JSON string or file
    
    Args:
        repos_config: JSON string or path to JSON file with repositories information
        
    Returns:
        List of repository configurations with username, owner, and repo keys
    """
    repos = []
    
    # Check if the input is a file path
    if os.path.isfile(repos_config):
        with open(repos_config, 'r') as f:
            repos = json.load(f)
    else:
        # Try to parse as a JSON string
        try:
            repos = json.loads(repos_config)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format: {repos_config}")
    
    # Validate the format
    if not isinstance(repos, list):
        raise ValueError("Repositories configuration must be a list")
    
    for repo in repos:
        if not all(k in repo for k in ["username", "owner", "repo"]):
            raise ValueError(f"Each repository must have username, owner, and repo keys: {repo}")
            
    return repos

async def collect_data(args):
    """
    Function for collecting GitHub data
    """
    # Parse repositories configuration
    repos = parse_repos_config(args.repos)
    
    # Create save strategy based on arguments
    if args.output == 'csv':
        save_strategy = CSVSave(filename=args.output_file)
    elif args.output == 'neo4j':
        save_strategy = Neo4jSave(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password
        )
    else:  # default to print
        save_strategy = PrintSave()
    
    # Create collector with the chosen save strategy
    collector = Collector(
        days=args.days,
        github_token=os.environ.get("GITHUB_TOKEN"),
        save_strategy=save_strategy
    )
    
    # Collect data
    results = await collector.get(repos)
    
    print(f"Processed {len(results)} repositories")
    
    # Print any errors
    errors = {repo: data["error"] for repo, data in results.items() if "error" in data}
    if errors:
        print(f"Encountered errors in {len(errors)} repositories:")
        for repo, error in errors.items():
            print(f"  {repo}: {error}")

def analyze_data(args):
    """
    Function for analyzing GitHub data graph
    """
    # Create loader based on source
    if args.source == 'csv':
        if not args.file:
            raise ValueError("--file must be specified when source is csv")
        loader = CSVLoader(
            filepath=args.file
        )
    else:  # neo4j
        loader = Neo4jLoader(
            uri=args.neo4j_uri,
            username=args.neo4j_user,
            password=args.neo4j_password,
            query=args.neo4j_query
        )
    
    # Create and run analyzer
    analyzer = GraphAnalyzer(load_strategy=loader)
    analyzer.create().analyze()

async def main():
    """
    Main function for the GitHub graph explorer
    """
    args = parse_arguments()
    
    if args.mode == 'collect':
        await collect_data(args)
    elif args.mode == 'analyze':
        analyze_data(args)
    else:
        print("No mode specified. Use 'collect' or 'analyze'")
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())
