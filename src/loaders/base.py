from abc import ABC, abstractmethod
import networkx as nx
from typing import Dict, Any, List


class Loader(ABC):
    """
    Abstract base class for loading data into a networkx MultiGraph.
    
    This class defines the interface that all loader implementations must follow.
    Subclasses should implement the load_data method to retrieve and format data
    from various sources.
    """
    
    @abstractmethod
    def load_data(self) -> List[Dict[str, Any]]:
        """
        Load data from the source and return it as a list of relationship dictionaries.
        
        Returns:
            List of dictionaries, each representing a relationship
        """
        pass
    
    def create_graph(self) -> nx.MultiGraph:
        """
        Creates a networkx MultiGraph from the loaded data.
        
        Returns:
            A networkx MultiGraph containing the relationships
        """
        G = nx.Graph()
        
        # Load relationships from the data source
        relationships = self.load_data()
        
        # Add each relationship to the graph
        for rel in relationships:
            source = rel.get('source')
            target = rel.get('target')
            
            # Skip if source or target is missing
            if not source or not target:
                continue
                
            # Create edge with all attributes from the relationship
            G.add_edge(
                source,
                target,
                **{k: v for k, v in rel.items() if k not in ('source', 'target')}
            )
            
        return G