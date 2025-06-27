# Cobalt Repository Social Network Analysis

This directory contains tools and notebooks for analyzing all user activity on the `icebreakerlabs/cobalt` repository using social network analysis techniques.

## Overview

The analysis provides comprehensive insights into:
- **Team collaboration patterns** - Who works with whom
- **User centrality and importance** - Key players in the project
- **Activity distribution** - How work is distributed across the team
- **Network health metrics** - Overall team collaboration effectiveness
- **Engineering metrics** - Code review patterns, issue management, etc.

## Files

- `cobalt-repo-analysis.ipynb` - Main Jupyter notebook for analysis and visualization
- `src/cobalt_analyzer.py` - Helper script for automated data collection

## Quick Start

### 1. Prerequisites

Make sure you have:
- GitHub Personal Access Token with appropriate permissions
- Python environment with required packages (see main README)
- Access to the `icebreakerlabs/cobalt` repository

### 2. Set up your GitHub token

```bash
export GITHUB_TOKEN=your_github_token_here
```

### 3. Run the automated data collection

```bash
# For last 30 days (default)
uv run src/cobalt_analyzer.py

# For custom time period (e.g., last 60 days)
uv run src/cobalt_analyzer.py 60
```

This will:
- Discover all contributors, collaborators, and recent activity users
- Create a configuration file for data collection
- Collect GitHub activity data for all users
- Save the data to CSV files

### 4. Run the analysis notebook

```bash
uv run jupyter lab
```

Then open `notebooks/cobalt-repo-analysis.ipynb` and run all cells.

## What the Analysis Provides

### Social Network Metrics

- **Degree Centrality** - How many direct connections each user has
- **Betweenness Centrality** - How much a user acts as a bridge between others
- **Closeness Centrality** - How close a user is to all other users in the network
- **Eigenvector Centrality** - How important a user is based on their connections' importance
- **Clustering Coefficient** - How tightly connected a user's neighbors are

### Engineering Metrics

- **Activity Types** - Issues created, PRs opened, reviews given, comments made
- **Collaboration Patterns** - Who reviews whose work, who comments on what
- **Temporal Analysis** - How activity patterns change over time
- **Team Structure** - Identification of core team members vs. peripheral contributors

### Network Health Indicators

- **Network Density** - Overall level of collaboration
- **Average Clustering** - How much the team forms tight-knit groups
- **Connected Components** - Whether the team is fragmented or unified
- **Average Path Length** - How many steps it takes to connect any two team members

## Output Files

The analysis generates several CSV files in the `data/` directory:

- `cobalt_activity_YYYYMMDD_HHMMSS.csv` - Raw activity data
- `cobalt_sna_metrics_YYYYMMDD_HHMMSS.csv` - Social network analysis metrics
- `cobalt_network_edges_YYYYMMDD_HHMMSS.csv` - Network connections
- `cobalt_analysis_summary_YYYYMMDD_HHMMSS.csv` - Summary statistics

## Customization

### Adjusting the Time Period

In the notebook, modify the `DAYS_BACK` variable:

```python
DAYS_BACK = 60  # Analyze last 60 days instead of 30
```

### Adding More Repositories

To analyze multiple repositories, modify the `CobaltAnalyzer` class or create a new analyzer for different repositories.

### Custom Visualizations

The notebook includes comprehensive visualizations, but you can add custom plots by:

1. Adding new cells to the notebook
2. Using the `sna_metrics` DataFrame for user-level analysis
3. Using the `G` NetworkX graph for network-level analysis
4. Using the raw `df` DataFrame for activity-level analysis

## Key Insights You'll Get

### Team Dynamics
- **Central Players** - Users who are most connected and important
- **Information Brokers** - Users who bridge different parts of the team
- **Isolated Members** - Users who might need more integration
- **Collaboration Clusters** - Natural team formations

### Engineering Patterns
- **Review Patterns** - Who reviews whose work
- **Issue Management** - How issues are created and resolved
- **Discussion Patterns** - How team members communicate
- **Activity Distribution** - How work is spread across the team

### Recommendations
- **Bottleneck Identification** - Users who might be overloaded
- **Collaboration Opportunities** - Where to encourage more interaction
- **Team Health** - Overall assessment of team collaboration effectiveness

## Troubleshooting

### No Data Found
- Check that your GitHub token has appropriate permissions
- Verify you have access to the repository
- Try increasing the time period if there's been little recent activity

### API Rate Limits
- GitHub has rate limits on API calls
- The script handles pagination automatically
- For large repositories, the data collection may take some time

### Missing Users
- The tool discovers users through multiple methods (contributors, collaborators, recent activity)
- If a user hasn't been active recently, they might not appear in the analysis
- You can manually add users to the configuration file if needed

## Advanced Usage

### Custom Network Analysis

You can extend the analysis by adding custom metrics:

```python
# Add custom centrality measures
from networkx.algorithms.centrality import harmonic_centrality
harmonic_cent = harmonic_centrality(G)
```

### Time-based Analysis

For temporal analysis, you can split the data by time periods:

```python
# Analyze weekly patterns
df['week'] = pd.to_datetime(df['created_at']).dt.isocalendar().week
weekly_activity = df.groupby('week').size()
```

### Comparative Analysis

To compare multiple repositories or time periods, run the analysis multiple times and compare the results.

## Contributing

To extend this analysis:

1. Add new metrics to the `calculate_sna_metrics` function
2. Create new visualizations in the `create_network_visualizations` function
3. Add new insights to the `generate_insights` function
4. Update this README with new features

## References

- [NetworkX Documentation](https://networkx.org/documentation/)
- [Social Network Analysis in Python](https://networkx.org/documentation/stable/reference/algorithms/centrality.html)
- [GitHub API Documentation](https://docs.github.com/en/rest) 