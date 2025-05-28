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


### Collecting Data
```
# Print output (default: last 7 days)
uv run main.py collect --repos data/repos.json --days 30 --output print

# CSV output
uv run main.py collect --repos data/repos.json --days 30 --output csv --output-file github_data.csv

# Neo4j output
uv run main.py collect --repos data/repos.json --days 15 --output neo4j --neo4j-uri bolt://localhost:7687

# Using specific date ranges instead of days (recommended for precise control)
uv run main.py collect --repos data/repos.json --since-iso 2025-05-01 --until-iso 2025-05-20 --output csv --output-file github_data.csv

# Using full ISO datetime format
uv run main.py collect --repos data/repos.json --since-iso 2025-05-01T00:00:00 --until-iso 2025-05-20T23:59:59 --output neo4j
```

**Note**: The `days` parameter is handled at the top level (CLI/MCP) and converted to date ranges internally. The core components use `since_iso` and `until_iso` with defaults of 7 days ago to now.

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

### Using the GitHub Action

You can use this tool as a GitHub Action in your own repositories. This will automatically collect GitHub repository data and commit the results to your repository.

#### Setting up the Action

Create a `.github/workflows/collect-github-data.yml` file in your repository with the following content:

```yaml
name: Collect GitHub Graph Data

on:
  # Run daily at midnight
  schedule:
    - cron: '0 0 * * *'
  
  # Allow manual trigger
  workflow_dispatch:

jobs:
  collect-data:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Run GitHub Graph Data Collector
        uses: yourusername/gh-graph-explore@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          repos_file: 'repos.json'
          days: '1'
          output_file: 'github_data.csv'
          commit_message: 'Update GitHub repository data [Skip CI]'
```

#### Creating a repos.json file

Create a `repos.json` file in the root of your repository with the following structure:

```json
[
  {
    "username": "dependabot",
    "owner": "octocat",
    "repo": "Hello-World"
  },
  {
    "username": "user1",
    "owner": "organization1",
    "repo": "repo-name-1"
  },
  {
    "username": "user2",
    "owner": "organization2",
    "repo": "repo-name-2"
  }
]
```

#### Action Inputs

The GitHub Action accepts the following inputs:

- `github_token`: GitHub token with read access to repos (required)
- `repos_file`: Path to the JSON file containing repository information (default: `repos.json`)
- `days`: Number of days to look back (default: `1`, used only if `since_iso` is not provided)
- `since_iso`: Start date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) (optional)
- `until_iso`: End date in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) (optional)
- `output_file`: Output file path for CSV (default: `github_data.csv`)
- `commit_message`: Commit message for the CSV file update (default: `Update GitHub repository data`)

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

### Useful queries 
Filter by date
```neo4j
MATCH (source)-[rel:PR_REVIEW_APPROVED]->(target)  WHERE rel.created_at > "2025-04-15" RETURN * limit 100
```

Create a user Projection 
```neo4j

MATCH (u1:User)-[] -> (g:GitHubObject) <- []-(u2:User)
WHERE u1.name < u2.name
WITH u1, u2, collect(g.name) as gitobjects, count(g) as weight
MERGE (u1)-[r:CONNECTED]->(u2)
SET r.name = gitobjects, r.weight = weight
```

View the user projection
```neo4j
MATCH p = (u1:User)-[]-(u2:User) Return p limit 200
```