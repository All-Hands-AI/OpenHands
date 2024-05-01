
from abc import ABC, abstractmethod

class ExternalDbAdapter(ABC):
    """
    Interface for all external database adapters.
    """

    @abstractmethod
    def connect(self):
        """
        Establish a connection to the database.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Close the connection to the database.
        """
        pass

    @abstractmethod
    def query(self, query, params=None):
        """
        Perform a database query.
        :param query: The query string
        :param params: Optional parameters for the query
        :return: The results of the query
        """
        pass
