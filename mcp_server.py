import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.collector import Collector
from src.save_strategies import Neo4jSave
from src.graph_analyzer import GraphAnalyzer
from src.load_strategies import Neo4jLoader
from mcp import Server, Request, Response, ResponseStatus

# Default Neo4j connection settings
DEFAULT_NEO4J_URI = "bolt://neo4j:7687"
DEFAULT_NEO4J_USER = "neo4j"
DEFAULT_NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')

# Valid relationship types that can be filtered by
VALID_RELATIONSHIP_TYPES = [
    "DISCUSSION_COMMENT",
    "DISCUSSION_CREATED",
    "ISSUE_COMMENT",
    "ISSUE_CREATED",
    "PR_COMMENT",
    "PR_CREATED",
    "PR_REVIEW_APPROVED",
    "PR_REVIEW_COMMENTED"
]

class GithubGraphExplorerMCP(Server):
    """
    Model Context Protocol server for GitHub Graph Explorer.
    Provides endpoints for collecting and analyzing GitHub data.
    """
    
    def __init__(self):
        super().__init__()
        self.register_handler("collect", self.collect_data)
        self.register_handler("analyze", self.analyze_data)
        
    async def collect_data(self, request: Request) -> Response:
        """
        Collect GitHub data for specified users, repositories and time period.
        
        Request parameters:
            - user: GitHub username (required)
            - owner: Repository owner (required)
            - repo: Repository name (required)
            - days: Number of days to look back (default: 7)
        """
        try:
            # Validate required parameters
            user = request.get_parameter("user")
            owner = request.get_parameter("owner")
            repo = request.get_parameter("repo")
            days = request.get_parameter("days", 7)
            
            if not all([user, owner, repo]):
                return Response(
                    status=ResponseStatus.BAD_REQUEST,
                    body={"error": "Missing required parameters. Please provide 'user', 'owner', and 'repo'."}
                )
            
            # Parse days as integer
            try:
                days = int(days)
            except ValueError:
                return Response(
                    status=ResponseStatus.BAD_REQUEST,
                    body={"error": f"Invalid 'days' parameter: {days}. Must be an integer."}
                )
                
            # Create the repos config
            repos_config = [{"username": user, "owner": owner, "repo": repo}]
            
            # Create Neo4j save strategy (default for MCP server)
            save_strategy = Neo4jSave(
                uri=DEFAULT_NEO4J_URI,
                username=DEFAULT_NEO4J_USER,
                password=DEFAULT_NEO4J_PASSWORD
            )
            
            # Create collector with Neo4j save strategy
            collector = Collector(
                days=days,
                github_token=os.environ.get("GITHUB_TOKEN"),
                save_strategy=save_strategy
            )
            
            # Collect data
            results = await collector.get(repos_config)
            
            return Response(
                status=ResponseStatus.OK,
                body={
                    "message": f"Successfully processed repository {owner}/{repo} for user {user}",
                    "results": results,
                    "days_collected": days
                }
            )
            
        except Exception as e:
            return Response(
                status=ResponseStatus.INTERNAL_SERVER_ERROR,
                body={"error": f"Error collecting data: {str(e)}"}
            )

    async def analyze_data(self, request: Request) -> Response:
        """
        Analyze GitHub data with optional date filtering and relationship type filtering.
        
        Request parameters:
            - dates: List of dates to filter by (optional)
            - relationship_types: List of relationship types to filter by (optional)
        """
        try:
            # Get optional parameters
            dates = request.get_parameter("dates", [])
            relationship_types = request.get_parameter("relationship_types", [])
            
            # Validate relationship types if provided
            if relationship_types:
                invalid_types = [t for t in relationship_types if t not in VALID_RELATIONSHIP_TYPES]
                if invalid_types:
                    return Response(
                        status=ResponseStatus.BAD_REQUEST,
                        body={
                            "error": f"Invalid relationship types: {', '.join(invalid_types)}",
                            "valid_types": VALID_RELATIONSHIP_TYPES
                        }
                    )
            
            # Build Neo4j query based on filters
            query = self._build_neo4j_query(dates, relationship_types)
            
            # Create Neo4j loader with custom query
            loader = Neo4jLoader(
                uri=DEFAULT_NEO4J_URI,
                username=DEFAULT_NEO4J_USER,
                password=DEFAULT_NEO4J_PASSWORD,
                query=query
            )
            
            # Create and run analyzer
            analyzer = GraphAnalyzer(load_strategy=loader)
            analyzer.create()
            
            # Use the analyze method to get analysis results
            analysis_results = analyzer.analyze()
            
            return Response(
                status=ResponseStatus.OK,
                body={
                    "message": "Analysis completed successfully",
                    "analysis_results": analysis_results,
                    "filters": {
                        "dates": dates,
                        "relationship_types": relationship_types
                    }
                }
            )
            
        except Exception as e:
            return Response(
                status=ResponseStatus.INTERNAL_SERVER_ERROR,
                body={"error": f"Error analyzing data: {str(e)}"}
            )
    
    def _build_neo4j_query(self, dates: List[str], relationship_types: List[str]) -> str:
        """
        Build a Neo4j query based on filters.
        
        Args:
            dates: List of dates to filter by (ISO format)
            relationship_types: List of relationship types to filter by
            
        Returns:
            A Cypher query string
        """
        # Start with the base query
        query = "MATCH (source)-[rel]->(target)\n"
        conditions = []
        
        # Add date filters if provided
        if dates:
            date_conditions = []
            for date in dates:
                try:
                    # Validate the date format
                    datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_conditions.append(f'rel.created_at STARTS WITH "{date.split("T")[0]}"')
                except ValueError:
                    # If invalid date format, use it as-is (error will be caught at query execution)
                    date_conditions.append(f'rel.created_at STARTS WITH "{date}"')
            
            if date_conditions:
                conditions.append(f'({" OR ".join(date_conditions)})')
        
        # Add relationship type filters if provided
        if relationship_types:
            type_conditions = []
            for rel_type in relationship_types:
                type_conditions.append(f'TYPE(rel) = "{rel_type}"')
            
            if type_conditions:
                conditions.append(f'({" OR ".join(type_conditions)})')
        
        # Add WHERE clause if there are conditions
        if conditions:
            query += f'WHERE {" AND ".join(conditions)}\n'
        
        # Complete the query
        query += "RETURN source.name AS source, target.url AS target, \n"
        query += "       TYPE(rel) AS type, properties(rel) AS properties"
        
        return query

async def main():
    """
    Start the MCP server
    """
    # Create and run the MCP server
    server = GithubGraphExplorerMCP()
    
    # Default configuration
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "8080"))
    
    print(f"Starting GitHub Graph Explorer MCP server on {host}:{port}")
    await server.serve(host=host, port=port)

if __name__ == "__main__":
    # Make sure networkx is imported in the main module
    import networkx as nx
    
    # Run the server
    asyncio.run(main())