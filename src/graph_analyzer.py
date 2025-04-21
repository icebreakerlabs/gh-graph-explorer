import networkx as nx
from typing import Optional
from .loaders import Loader

class GraphAnalyzer:
    """
    Class responsible for creating and analyzing a networkx DiGraph using a loader strategy.
    
    This class takes a loader implementation and uses it to create a networkx DiGraph
    representing relationships between entities.
    """
    
    def __init__(self, load_strategy: Loader):
        """
        Initialize the GraphAnalyzer with a loader strategy.
        
        Args:
            load_strategy: A concrete implementation of the Loader abstract class
        """
        self.load_strategy = load_strategy
        self.graph = None
    
    def create(self) -> 'GraphAnalyzer':
        """
        Create a networkx DiGraph using the configured loader strategy and store it in memory.
        
        Returns:
            Self reference for method chaining
        """
        self.graph = self.load_strategy.create_graph()
        return self
        
    def analyze(self) -> None:
        """
        Print analysis information about the graph including the number of nodes and edges.
        """
        if self.graph is None:
            print("No graph has been created yet. Call create() first.")
            return
            
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        
        print(f"Graph Analysis:")
        print(f"Number of nodes: {num_nodes}")
        print(f"Number of edges: {num_edges}")