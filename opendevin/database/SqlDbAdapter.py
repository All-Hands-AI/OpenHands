
import sqlite3
from .ExternalDbAdapter import ExternalDbAdapter

class SqlDbAdapter(ExternalDbAdapter):
    """
    An adapter class to handle SQLite database operations, complies with the ExternalDbAdapter interface.
    """
    def __init__(self, db_path):
        """
        Initialize the SqlDbAdapter with the given database path.
        
        Args:
        db_path (str): The filesystem path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """
        Establishes a connection to the SQLite database specified by the db path.
        """
        self.connection = sqlite3.connect(self.db_path)

    def disconnect(self):
        """
        Closes the connection to the SQLite database if it is open.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def query(self, query, params=None):
        """
        Executes a SQL query on the SQLite database using the provided query and parameters.
        
        Args:
        query (str): The SQL query to be executed.
        params (tuple, optional): The parameters to be used with the SQL query. Defaults to None.
        
        Returns:
        list: The fetched results from the database after the query execution.
        """
        cursor = self.connection.cursor()
        result = cursor.execute(query, params or ())
        return result.fetchall()
