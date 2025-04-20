from abc import ABC, abstractmethod
import csv
import os
from datetime import datetime
from typing import List
from edge import Edge

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
        self.headers = ['type', 'title', 'created_at', 'login', 'url', 'parent_url']
        
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