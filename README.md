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


python main.py --repos data/repos.json --days 30 --output print
python main.py --repos data/repos.json --days 30 --output csv --output-file github_data.csv

