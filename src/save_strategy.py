from abc import ABC, abstractmethod
import csv
import os
from datetime import datetime
from .edge import Edge

# Import Neo4j driver
from neo4j import GraphDatabase

class SaveStrategy(ABC):
    """
    Abstract base class for edge saving strategies
    """
    @abstractmethod
    def save(self, edge: Edge) -> None:
        """
        Save an edge using the strategy's implementation
        
        Args:
            edge: The Edge object to save
        """
        pass
    
    def finalize(self) -> None:
        """
        Optional method to finalize the saving process (e.g., close files)
        """
        pass


class PrintSave(SaveStrategy):
    """
    Strategy that saves edges by printing them to the console
    """
    def save(self, edge: Edge) -> None:
        """
        Save an edge by printing it to the console
        
        Args:
            edge: The Edge object to print
        """
        print(edge)


class CSVSave(SaveStrategy):
    """
    Strategy that saves edges to a CSV file
    """
    def __init__(self, filename: str = None):
        """
        Initialize CSV save strategy with a filename
        
        Args:
            filename: Name of the CSV file to save to. If None, a default 
                     filename with current timestamp will be used.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_edges_{timestamp}.csv"
        
        self.filename = filename
        self.file = None
        self.writer = None
        self.headers = ['source', 'target', 'type', 'title', 'created_at', 'url']
        
    def _init_file(self):
        """
        Initialize the CSV file and writer
        """
        file_exists = os.path.isfile(self.filename)
        
        self.file = open(self.filename, 'a', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=self.headers)
        
        # Write headers only if creating a new file
        if not file_exists:
            self.writer.writeheader()
    
    def save(self, edge: Edge) -> None:
        """
        Save an edge to the CSV file
        
        Args:
            edge: The Edge object to save
        """
        if self.writer is None:
            self._init_file()
            
        self.writer.writerow(edge.to_row())
    
    def finalize(self) -> None:
        """
        Close the CSV file
        """
        if self.file:
            self.file.close()


class Neo4jSave(SaveStrategy):
    """
    Strategy that saves edges to a Neo4j database
    """
    def __init__(self, uri: str = "bolt://neo4j:7687", 
                 username: str = "neo4j", 
                 password: str = "password"):
        """
        Initialize Neo4j save strategy with connection details
        
        Args:
            uri: URI for the Neo4j database
            username: Username for Neo4j authentication
            password: Password for Neo4j authentication
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._connect()
        
    def _connect(self):
        """
        Establish connection to Neo4j database
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            raise
            
    def save(self, edge: Edge) -> None:
        """
        Save an edge to Neo4j database
        
        Args:
            edge: The Edge object to save
        """
        if not self.driver:
            self._connect()
            
        with self.driver.session() as session:
            # Create a Cypher query to save the edge
            # This will create or match the source and target nodes and create a relationship between them
            result = session.execute_write(self._create_edge, edge)
    
    def _create_edge(self, tx, edge: Edge) -> None:
        """
        Create an edge in the Neo4j database using a transaction
        
        Args:
            tx: Neo4j transaction
            edge: The Edge object to save
            
        Returns:
            The number of edges created (0 if edge already existed)
        """
        # Create a query using MERGE for both nodes and the relationship
        # This ensures that duplicates are not created
        properties = edge.to_row()
        relationship_type = properties['type'].upper().replace(" ", "_")
        
        query = (
            "MERGE (source:User {name: $source_name}) "
            "MERGE (target:GitHubObject {url: $target_url}) "
            f"MERGE (source)-[r:{relationship_type} {{url: $url}}]->(target) "
            "ON CREATE SET r.title = $title, "
            "r.created_at = $created_at "
            "RETURN count(r) as edges_count"
        )
        result = tx.run(query, 
               source_name=edge.source(), 
               target_url=edge.target(), 
               title=edge.title(),
               created_at=edge.created_at(),
               url=edge.url())
        
        summary = result.consume()
        return summary.counters.relationships_created
    
    def finalize(self) -> None:
        """
        Close the Neo4j connection
        """
        if self.driver:
            self.driver.close()