import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.collector import Collector
from src.save_strategies import Neo4jSave
from src.graph_analyzer import GraphAnalyzer
from src.load_strategies import Neo4jLoader

from fastmcp import FastMCP
mcp = FastMCP(name="GitHub Graph Explorer", version="1.0.0")


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


@mcp.tool("collect")
async def collect(
    user: str,
    owner: str,
    repo: str,
    days: Optional[int] = 7
) -> dict:
    """
    Collect GitHub data for specified users, repositories and time period.
    
    Request parameters:
        - user: GitHub username (required)
        - owner: Repository owner (required)
        - repo: Repository name (required)
        - days: Number of days to look back (default: 7)
    """
    # Validate required parameters
    if not all([user, owner, repo]):
        return {}
    
    # Parse days as integer
    try:
        days = int(days)
    except ValueError:
        return {}

        
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
    
    return {
            "message": f"Successfully processed repository {owner}/{repo} for user {user}",
            "results": results,
            "days_collected": days
        }
        


@mcp.tool("analyze")
async def analyze(
    dates: Optional[List[str]] = None,
    relationship_types: Optional[List[str]] = None
) -> dict:
    """
    Analyze GitHub data with optional date filtering and relationship type filtering.
    
    Request parameters:
        - dates: List of dates to filter by (optional)
        - relationship_types: List of relationship types to filter by (optional)
    """
    
    # Validate relationship types if provided
    if relationship_types:
        invalid_types = [t for t in relationship_types if t not in VALID_RELATIONSHIP_TYPES]
        if invalid_types:
            return {
                    "error": f"Invalid relationship types: {', '.join(invalid_types)}",
                    "valid_types": VALID_RELATIONSHIP_TYPES
                }
    
    # Build Neo4j query based on filters
    query = _build_neo4j_query(dates, relationship_types)
    
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
    
    return {
            "message": "Analysis completed successfully",
            "analysis_results": analysis_results,
            "filters": {
                "dates": dates,
                "relationship_types": relationship_types
            }
        }
        
def _build_neo4j_query(dates: List[str], relationship_types: List[str]) -> str:
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


# Main entry point
if __name__ == "__main__":
    # Bind to all interfaces (0.0.0.0) to allow external connections
    asyncio.run(mcp.run(host="0.0.0.0", port=8000, transport="sse"))