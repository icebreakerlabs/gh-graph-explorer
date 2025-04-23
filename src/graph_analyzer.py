import networkx as nx
from typing import Optional, Dict, List, Set, Any
from .load_strategies import Loader
from collections import Counter

class GraphAnalyzer:
    """
    Class responsible for creating and analyzing a networkx DiGraph using a loader strategy.
    
    This class takes a loader implementation and uses it to create a networkx DiGraph
    representing relationships between entities in a GitHub social network.
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
    
    def _is_username(self, node: str) -> bool:
        """
        Determine if a node represents a GitHub username.
        
        For now, this is a simple heuristic that assumes nodes without slashes or dots
        that don't end with common file extensions are usernames.
        
        Args:
            node: Node identifier to check
            
        Returns:
            Boolean indicating if the node is likely a username
        """
        # This is a very simple heuristic and might need refinement based on your data
        if isinstance(node, str):
            if '/' not in node and not node.endswith(('.js', '.py', '.md', '.txt', '.html', '.css')):
                return True
        return False
    
    def _is_resource(self, node: str) -> bool:
        """
        Determine if a node represents a GitHub resource (repo, file, etc).
        
        Args:
            node: Node identifier to check
            
        Returns:
            Boolean indicating if the node is likely a resource
        """
        return not self._is_username(node)
        
    def analyze(self) -> None:
        """
        Print analysis information about the graph including:
        - Basic stats (nodes, edges)
        - Degree statistics
        - Centrality measures 
        - Connected components
        - Clustering information
        - Path analysis
        - GitHub-specific analysis
        - Connectivity analysis
        - Disconnected nodes analysis
        """
        if self.graph is None:
            print("No graph has been created yet. Call create() first.")
            return
            
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        
        print(f"GitHub Network Analysis:")
        print(f"Number of nodes: {num_nodes}")
        print(f"Number of edges: {num_edges}")
        
        # Skip analysis for empty graphs
        if num_nodes == 0:
            print("Graph is empty. No further analysis available.")
            return
        
        # Count users vs resources
        users = [n for n in self.graph.nodes() if self._is_username(n)]
        resources = [n for n in self.graph.nodes() if self._is_resource(n)]
        
        print(f"\nNode Types:")
        print(f"Users: {len(users)} ({len(users)/num_nodes*100:.1f}%)")
        print(f"Resources: {len(resources)} ({len(resources)/num_nodes*100:.1f}%)")
            
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
        
        # Get top users by centrality
        top_users_by_degree = [(n, c) for n, c in degree_centrality.items() 
                              if self._is_username(n)]
        top_users_by_degree = sorted(top_users_by_degree, key=lambda x: x[1], reverse=True)[:5]
        
        print("Top users by degree centrality:")
        for node, centrality in top_users_by_degree:
            print(f"  User: {node}, Centrality: {centrality:.4f}")
        
        # Get top resources by centrality
        top_resources_by_degree = [(n, c) for n, c in degree_centrality.items() 
                                  if self._is_resource(n)]
        top_resources_by_degree = sorted(top_resources_by_degree, key=lambda x: x[1], reverse=True)[:5]
        
        print("\nTop resources by degree centrality:")
        for node, centrality in top_resources_by_degree:
            print(f"  Resource: {node}, Centrality: {centrality:.4f}")
        
        # Connectivity analysis
        print("\nConnectivity Analysis:")
        
        # For directed graphs, we analyze weakly and strongly connected components
        if nx.is_directed(self.graph):
            weak_components = list(nx.weakly_connected_components(self.graph))
            strong_components = list(nx.strongly_connected_components(self.graph))
            
            print(f"Weakly connected components: {len(weak_components)}")
            print(f"Largest weakly connected component: {len(max(weak_components, key=len))} nodes")
            
            print(f"Strongly connected components: {len(strong_components)}")
            print(f"Largest strongly connected component: {len(max(strong_components, key=len))} nodes")
            
            # Calculate the giant component ratio
            giant_ratio = len(max(weak_components, key=len)) / num_nodes
            print(f"Giant component ratio: {giant_ratio:.2f}")
        else:
            # For undirected graphs
            components = list(nx.connected_components(self.graph))
            print(f"Connected components: {len(components)}")
            print(f"Largest connected component: {len(max(components, key=len))} nodes")
            
            # Calculate the giant component ratio
            giant_ratio = len(max(components, key=len)) / num_nodes
            print(f"Giant component ratio: {giant_ratio:.2f}")
        
        # Disconnected nodes analysis
        print("\nDisconnected Nodes Analysis:")
        
        # Get nodes that are not part of the largest connected component
        if nx.is_directed(self.graph):
            weak_components = list(nx.weakly_connected_components(self.graph))
            if weak_components:
                largest_component = max(weak_components, key=len)
                disconnected_nodes = [n for n in self.graph.nodes() if n not in largest_component]
        else:
            components = list(nx.connected_components(self.graph))
            if components:
                largest_component = max(components, key=len)
                disconnected_nodes = [n for n in self.graph.nodes() if n not in largest_component]
            else:
                disconnected_nodes = []
        
        print(f"Nodes not connected to the largest component: {len(disconnected_nodes)} ({len(disconnected_nodes)/num_nodes*100:.1f}% of total)")
        
        # Categorize disconnected nodes
        disconnected_users = [n for n in disconnected_nodes if self._is_username(n)]
        disconnected_resources = [n for n in disconnected_nodes if self._is_resource(n)]
        
        print(f"Disconnected users: {len(disconnected_users)}")
        print(f"Disconnected resources: {len(disconnected_resources)}")
        
        if disconnected_users and len(disconnected_users) <= 5:
            print("Sample disconnected users:")
            for user in disconnected_users[:5]:
                print(f"  {user}")
        
        # Also still check for completely isolated nodes (degree 0)
        isolated_nodes = list(nx.isolates(self.graph))
        print(f"Completely isolated nodes (degree 0): {len(isolated_nodes)} ({len(isolated_nodes)/num_nodes*100:.1f}%)")
        
        # Find nodes with only incoming or only outgoing connections
        if nx.is_directed(self.graph):
            only_incoming = [n for n in self.graph.nodes() 
                            if self.graph.in_degree(n) > 0 and self.graph.out_degree(n) == 0]
            only_outgoing = [n for n in self.graph.nodes() 
                            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) > 0]
            
            print(f"Nodes with only incoming connections: {len(only_incoming)}")
            print(f"Nodes with only outgoing connections: {len(only_outgoing)}")
        
        # Clustering coefficient - how nodes tend to cluster together
        try:
            avg_clustering = nx.average_clustering(self.graph)
            print(f"\nAverage clustering coefficient: {avg_clustering:.4f}")
        except Exception as e:
            print(f"Couldn't calculate clustering coefficient: {e}")
