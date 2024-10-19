from openhands.core.config.llm_config import LLMConfig
from openhands.memory.base_memory import Memory
from openhands.memory.memory import LongTermMemory

TOP_K = 10


class RecallMemory(Memory):
    """Facilitates retrieval of information from LongTermMemory."""

    def __init__(
        self,
        long_term_memory: LongTermMemory,
        llm_config: LLMConfig,
        top_k: int = TOP_K,
    ):
        """
        Initialize RecallMemory with a reference to LongTermMemory.

        Args:
            archival_memory (LongTermMemory): The archival memory instance to query.
            embedding_model (any): The embedding model used for vector transformations.
            top_k (int): Number of top results to retrieve.
        """
        self.long_term_memory = long_term_memory
        self.llm_config = llm_config
        self.top_k = top_k

    def to_dict(self) -> dict:
        return {
            'long_term_memory': self.long_term_memory.to_dict(),
            'top_k': self.top_k,
        }

    def from_dict(self, data: dict) -> None:
        self.long_term_memory.from_dict(data.get('long_term_memory', {}))
        self.top_k = data.get('top_k', 10)

    def __str__(self) -> str:
        return f'RecallMemory with top_k={self.top_k}'

    def text_search(
        self, query: str, count: int | None = None, start: int | None = None
    ) -> tuple[list[str], int]:
        """
        Perform a text-based search on LongTermMemory.

        Args:
            query (str): The text query to search for.
            count (Optional[int]): Number of results to return.
            start (Optional[int]): Pagination start index.

        Returns:
            Tuple[List[str], int]: A tuple containing the list of matching messages and the total number of matches.
        """
        return self.long_term_memory.text_search(query, count, start)

    def date_search(
        self,
        start_date: str,
        end_date: str,
        count: int | None = None,
        start: int | None = None,
    ) -> tuple[list[str], int]:
        """
        Perform a date-based search on LongTermMemory.

        Args:
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.
            count (Optional[int]): Number of results to return.
            start (Optional[int]): Pagination start index.

        Returns:
            Tuple[List[str], int]: A tuple containing the list of matching messages and the total number of matches.
        """
        return self.long_term_memory.date_search(start_date, end_date, count, start)

    def embedding_search(
        self, query: str, count: int | None = None, start: int | None = None
    ) -> tuple[list[str], int]:
        """
        Perform an embedding-based semantic search on LongTermMemory.

        Args:
            query (str): The query string for semantic search.
            count (Optional[int]): Number of results to return.
            start (Optional[int]): Pagination start index.

        Returns:
            Tuple[List[str], int]: A tuple containing the list of semantically similar messages and the total number of matches.
        """
        return self.long_term_memory.search(query, count, start)
