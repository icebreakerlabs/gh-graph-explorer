# 🚀 How to Add Repositories to Analysis

This guide shows you different ways to add repositories to your social network analysis.

## 📋 **Quick Summary**

| Method | Use Case | Difficulty | Best For |
|--------|----------|------------|----------|
| [Crypto Analyzer Manual Repos](#1-crypto-analysis-add-specific-repos) | Add specific repos to crypto analysis | Easy | Adding well-known crypto repos |
| [Icebreaker Repos Modification](#2-icebreaker-analysis-add-repos) | Add repos to icebreaker analysis | Easy | Adding team/org repositories |
| [Custom Configuration File](#3-custom-configuration-file) | Complete control over analysis | Medium | Custom analysis setups |
| [Direct Collection](#4-direct-data-collection) | Use existing repo config | Easy | Quick analysis of known repos |

---

## 🎯 **1. Crypto Analysis: Add Specific Repos**

### **Method A: Using the Enhanced Crypto Analyzer**

```python
# Run this in notebooks directory
python add_repos_example.py
```

Or programmatically:

```python
from crypto_repo_analyzer import CryptoRepoAnalyzer

# Define repositories you want to add
manual_repos = [
    {"owner": "ethereum", "repo": "go-ethereum", "ecosystem": "ethereum"},
    {"owner": "bitcoin", "repo": "bitcoin", "ecosystem": "bitcoin"},
    {"owner": "solana-labs", "repo": "solana", "ecosystem": "solana"},
    {"owner": "your-org", "repo": "your-repo", "ecosystem": "your-ecosystem"}
]

analyzer = CryptoRepoAnalyzer(github_token)
results = analyzer.run_full_analysis(
    months_back=6,
    target_repo_count=20,  # Total repos including manual ones
    manual_repos=manual_repos
)
```

### **Method B: Modify the Crypto Analyzer Directly**

Edit `crypto_repo_analyzer.py` and modify the `select_diverse_repos` method to include your specific repositories.

---

## 🏛️ **2. Icebreaker Analysis: Add Repos**

### **Add to Extended Cobalt Analysis**

Edit `extended_cobalt_analysis.py`, line 44-47:

```python
self.repositories = [
    {'owner': 'icebreakerlabs', 'repo': 'cobalt'},
    {'owner': 'icebreakerlabs', 'repo': 'columbo'},
    # Add your repositories here:
    {'owner': 'your-org', 'repo': 'your-repo'},
    {'owner': 'another-org', 'repo': 'another-repo'}
]
```

Then run:
```bash
python extended_cobalt_analysis.py
```

---

## ⚙️ **3. Custom Configuration File**

### **Create Custom repos.json**

Create a file like `custom_repos_example.json`:

```json
[
  {
    "username": "contributor1",
    "owner": "your-org",
    "repo": "your-repo"
  },
  {
    "username": "contributor2", 
    "owner": "your-org",
    "repo": "your-repo"
  },
  {
    "username": "maintainer1",
    "owner": "another-org",
    "repo": "another-repo"
  }
]
```

### **Use with Main Tool**

```bash
# From project root
uv run main.py collect --repos notebooks/custom_repos_example.json --output csv --output-file my_analysis.csv

# Then analyze
uv run main.py analyze --source csv --file my_analysis.csv
```

---

## 🔍 **4. Direct Data Collection**

### **Quick Analysis of Specific Repos**

```bash
# 1. Create a simple repos.json file with your repositories
echo '[
  {"username": "user1", "owner": "org1", "repo": "repo1"},
  {"username": "user2", "owner": "org2", "repo": "repo2"}
]' > my_repos.json

# 2. Collect data
uv run main.py collect --repos my_repos.json --since-iso 2024-01-01 --until-iso 2024-12-31 --output csv --output-file my_data.csv

# 3. Analyze
uv run main.py analyze --source csv --file my_data.csv
```

---

## 📊 **Interactive Analysis with New Repos**

After adding repositories using any method above, you can use the interactive dashboard:

### **Jupyter Notebook**
```bash
uv run jupyter lab
# Open interactive-crypto-dashboard.ipynb
```

### **Standalone HTML**
```bash
cd notebooks
python interactive_demo.py
```

---

## 💡 **Tips & Best Practices**

### **🎯 Repository Selection**
- **Start small**: Begin with 5-10 repositories to test
- **Related repositories**: Choose repos that might have overlapping contributors
- **Active repositories**: Select repos with recent activity for meaningful analysis
- **Diverse ecosystems**: Mix different types of projects for interesting insights

### **⚡ Performance Considerations**
- **Limit contributors**: For large repos, the analyzer automatically limits to 20 contributors per repo
- **Date ranges**: Use shorter date ranges (3-6 months) for faster analysis
- **Repository count**: 15-25 repositories is usually optimal for analysis

### **🔧 Configuration Tips**
- **Username discovery**: The analyzers automatically discover contributors, collaborators, and recent activity users
- **Manual specification**: You can manually specify usernames if you know specific contributors to focus on
- **Ecosystem labeling**: Use meaningful ecosystem labels for better visualization grouping

---

## 🚨 **Troubleshooting**

### **Common Issues**

**❌ "Repository not found"**
- Check repository name spelling
- Ensure repository is public or you have access
- Verify GitHub token has necessary permissions

**❌ "No data collected"**
- Check date ranges (repositories might not have activity in specified period)
- Verify contributors exist and have activity
- Check GitHub API rate limits

**❌ "Empty analysis results"**
- Ensure repositories have recent activity
- Check that contributors have interactions (PRs, issues, comments)
- Verify date range includes active periods

### **GitHub API Limits**
- The tool respects GitHub API rate limits
- Use shorter date ranges for large repositories
- Consider running analysis during off-peak hours

---

## 🎉 **Examples**

### **Example 1: DeFi Projects Analysis**
```python
defi_repos = [
    {"owner": "uniswap", "repo": "v3-core", "ecosystem": "defi"},
    {"owner": "aave", "repo": "aave-v3-core", "ecosystem": "defi"},
    {"owner": "compound-finance", "repo": "compound-protocol", "ecosystem": "defi"}
]
```

### **Example 2: Your Team's Repositories**
```python
team_repos = [
    {"owner": "your-org", "repo": "frontend-app", "ecosystem": "frontend"},
    {"owner": "your-org", "repo": "backend-api", "ecosystem": "backend"},
    {"owner": "your-org", "repo": "mobile-app", "ecosystem": "mobile"}
]
```

### **Example 3: Open Source Projects**
```python
oss_repos = [
    {"owner": "facebook", "repo": "react", "ecosystem": "frontend"},
    {"owner": "microsoft", "repo": "vscode", "ecosystem": "tools"},
    {"owner": "nodejs", "repo": "node", "ecosystem": "runtime"}
]
```

---

## 🔄 **Next Steps**

1. **Choose your method** based on your use case
2. **Add your repositories** using one of the methods above
3. **Run the analysis** to collect data
4. **Explore with interactive dashboard** to gain insights
5. **Export results** for further analysis or reporting

Happy analyzing! 🎉 