from openhands.core.config.llm_config import LLMConfig
from openhands.memory.base_memory import Memory
from openhands.memory.memory import LongTermMemory
from openhands.events.event import Event

TOP_K = 10


class ConversationMemory(Memory):
    """Allows the agent to recall events from its entire history."""

    def __init__(
        self,
        memory_config: LLMConfig,
        history: list[Event],
    ):
        """
        Initialize ConversationMemory with a reference to history and long-term memory.

        Args:
        - history: The history of the current agent conversation.
        - llm_config: The LLM configuration.
        - top_k: Number of top results to retrieve.
        """
        self.history = history or []
        self.llm_config = memory_config
        self.top_k = TOP_K

    def to_dict(self) -> dict:
        # return a dict with key = event.id, value = event.to_dict()
        return {event.id: event.to_dict() for event in self.history}

    def from_dict(self, data: dict) -> None:
        self.history = [Event.from_dict(event) for event in data.values()]

    def __str__(self) -> str:
        return f'ConversationMemory with {len(self.history)} events'

    def text_search(
        self, query: str, count: int | None = None, start: int | None = None
    ) -> tuple[list[str], int]:
        """
        Perform a text-based search on LongTermMemory.

        Args:
            query: The text query to search for.
            count: Number of results to return.
            start: Pagination start index.

        Returns:
            A tuple containing the list of matching messages and the total number of matches.
        """
        # return self.long_term_memory.text_search(query, count, start)
        pass

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
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            count: Number of results to return.
            start: Pagination start index.

        Returns:
            A tuple containing the list of matching messages and the total number of matches.
        """
        # return self.long_term_memory.date_search(start_date, end_date, count, start)
        pass

    def embedding_search(
        self, query: str, count: int | None = None, start: int | None = None
    ) -> tuple[list[str], int]:
        """
        Perform an embedding-based semantic search on LongTermMemory.

        Args:
            query: The query string for semantic search.
            count: Number of results to return.
            start: Pagination start index.

        Returns:
            A tuple containing the list of semantically similar messages and the total number of matches.
        """
        # return self.long_term_memory.search(query, count, start)
        pass

    def reset(self) -> None:
        self.history = []
