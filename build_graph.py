
import github_graph_tools as gg
from datetime import datetime

collector = gg.GraphCollector(repository_names=['geramirez/some-repo'], since=datetime(2024, 4, 10))
graph_builder = gg.GraphBuilder(collector=collector)
graph_builder.build_and_write()
