# Graph explorer 

## Usage

### Get Data
1. pip install -r requirements.txt
1. Collect the data
    1. generate a github token with read permissions for repos + and set it in the GH_TOKEN env variable
    1. edit + run `build_graph.py`

### explore data
1. jupyter lab
1. load the csv file that was downloaded before


### Collecting Data (Same as Before)
```
# Print output
uv run main.py collect --repos data/repos.json --days 30 --output print

# CSV output
uv run main.py collect --repos data/repos.json --days 30 --output csv --output-file github_data.csv

# Neo4j output
uv run main.py collect --repos data/repos.json --days 30 --output neo4j --neo4j-uri bolt://localhost:7687
```

### Analyzing Data (New Functionality)
```
# Analyze from CSV file
uv run main.py analyze --source csv --file github_data.csv

# Analyze from Neo4j
uv run main.py analyze --source neo4j --neo4j-uri bolt://localhost:7687
```

The analyzer will use the appropriate loader (CSVLoader or Neo4jLoader) to load the data, create a networkx MultiGraph, and then use the GraphAnalyzer's analyze method to display information about the graph, such as the number of nodes and edges.

If you want to customize the Neo4j query for analysis, you can also use the --neo4j-query parameter:
```
uv run main.py analyze --source neo4j --neo4j-query "MATCH (source)-[rel]->(target)  WHERE rel.created_at > \"2025-04-01\" RETURN source.name AS source, target.url AS target, type(rel) AS type, properties(rel) AS properties" --neo4j-uri bolt://localhost:7687
```

### Setup with Claude Desktop
{
    "mcpServers": {
        "gh-graph-explorer": {
            "command": "uv",
            "args": [
                "--directory",
                "path to directory",
                "run",
                "mcp_server.py"
            ],
            "env": {
                "GITHUB_TOKEN": "*****",
                "NEO4J_PASSWORD": "password",
                "NEO4J_USERNAME": "neo4j",
                "NEO4J_URI": "bolt://localhost:7687"
            }
        }
      }
}