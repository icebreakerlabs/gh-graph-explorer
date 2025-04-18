from typing import Dict, Optional
from datetime import datetime


class Edge:
    """
    Class representing an edge in the GitHub work graph.
    """
    def __init__(
        self,
        edge_type: Optional[str] = None,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        login: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        Initialize an Edge with the given properties.

        Args:
            edge_type: Type of the edge (e.g., issue_created, pr_created)
            title: Title of the related GitHub object
            created_at: Creation timestamp
            login: User login associated with the edge
            url: URL of the GitHub object
        """
        self.type = edge_type
        self.title = title
        self.created_at = created_at
        self.login = login
        self.url = url
    
    def to_row(self) -> Dict[str, Optional[str]]:
        """
        Return a row representation of the edge data.
        
        Returns:
            Dictionary containing the edge data in row format
        """
        return {
            'type': self.type,
            'title': self.title,
            'created_at': self.created_at,
            'login': self.login,
            'url': self.url
        }
    
    def __str__(self) -> str:
        """
        Return a string representation of the edge.
        
        Returns:
            String representation of the edge
        """
        return f"Edge(type={self.type}, title={self.title}, created_at={self.created_at}, login={self.login}, url={self.url})"