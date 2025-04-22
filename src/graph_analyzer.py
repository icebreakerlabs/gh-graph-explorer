import networkx as nx
from typing import Optional
from .load_strategies import Loader

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
        Print analysis information about the graph including:
        - Basic stats (nodes, edges)
        - Degree statistics
        - Centrality measures 
        - Connected components
        - Clustering information
        - Path analysis
        """
        if self.graph is None:
            print("No graph has been created yet. Call create() first.")
            return
            
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        
        print(f"Graph Analysis:")
        print(f"Number of nodes: {num_nodes}")
        print(f"Number of edges: {num_edges}")
        
        # Skip analysis for empty graphs
        if num_nodes == 0:
            print("Graph is empty. No further analysis available.")
            return
            
        # Basic degree statistics
        degrees = [d for _, d in self.graph.degree()]
        avg_degree = sum(degrees) / num_nodes
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
        
        print("\nDegree Statistics:")
        print(f"Average degree: {avg_degree:.2f}")
        print(f"Maximum degree: {max_degree}")
        print(f"Minimum degree: {min_degree}")
        
        # Centrality measures
        print("\nCentrality Measures:")
        
        # Degree centrality - fraction of nodes a node is connected to
        degree_centrality = nx.degree_centrality(self.graph)
        top_by_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top nodes by degree centrality:")
        for node, centrality in top_by_degree:
            print(f"  Node: {node}, Centrality: {centrality:.4f}")
        
        # Betweenness centrality - nodes that act as bridges
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            top_by_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
            print("\nTop nodes by betweenness centrality:")
            for node, centrality in top_by_betweenness:
                print(f"  Node: {node}, Centrality: {centrality:.4f}")
        except Exception as e:
            print(f"Couldn't calculate betweenness centrality: {e}")
            
        # Connected components analysis
        if nx.is_directed(self.graph):
            print("\nDirected Graph Component Analysis:")
            strongly_connected = list(nx.strongly_connected_components(self.graph))
            print(f"Number of strongly connected components: {len(strongly_connected)}")
            if strongly_connected:
                print(f"Largest strongly connected component size: {len(strongly_connected[0])}")
            
            weakly_connected = list(nx.weakly_connected_components(self.graph))
            print(f"Number of weakly connected components: {len(weakly_connected)}")
            if weakly_connected:
                print(f"Largest weakly connected component size: {len(weakly_connected[0])}")
        else:
            print("\nUndirected Graph Component Analysis:")
            connected = list(nx.connected_components(self.graph))
            print(f"Number of connected components: {len(connected)}")
            if connected:
                print(f"Largest connected component size: {len(connected[0])}")
        
        # Clustering coefficient - how nodes tend to cluster together
        try:
            avg_clustering = nx.average_clustering(self.graph)
            print(f"\nAverage clustering coefficient: {avg_clustering:.4f}")
        except Exception as e:
            print(f"Couldn't calculate clustering coefficient: {e}")
            
        # Path analysis
        try:
            # For larger graphs, this can be computationally expensive
            if num_nodes < 1000:  # Only do this for smaller graphs
                diameter = nx.diameter(self.graph.to_undirected())
                avg_shortest_path = nx.average_shortest_path_length(self.graph)
                print(f"\nPath Analysis:")
                print(f"Diameter (longest shortest path): {diameter}")
                print(f"Average shortest path length: {avg_shortest_path:.4f}")
        except Exception as e:
            print(f"\nPath analysis skipped: {e}")
