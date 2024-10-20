from enum import Enum

from openhands.controller.state.state import State
from openhands.core.config.llm_config import LLMConfig
from openhands.events.action.agent import AgentSummarizeAction
from openhands.events.serialization.event import event_to_dict
from openhands.memory.base_memory import Memory

TOP_K = 10


class StorageType(Enum):
    IN_MEMORY = 'in-memory'
    VECTOR_DATABASE = 'vector'


class ConversationMemory(Memory):
    """Allows the agent to recall events from its entire history.

    This class handles the summarized events (from state.summary['start_id] to state.summary['end_id'])
    and slices the history to include only the events after the summary.
    """

    def __init__(
        self,
        memory_config: LLMConfig,
        state: State,
    ):
        """
        Initialize ConversationMemory with a reference to history and long-term memory.

        Args:
        - history: The history of the current agent conversation.
        - llm_config: The LLM configuration.
        - top_k: Number of top results to retrieve.
        """
        self.state = state
        self.llm_config = memory_config
        self.top_k = TOP_K

        # the number of messages that are hidden from the user
        self.hidden_message_count = 0

        self.storage_type = StorageType.IN_MEMORY

    def to_dict(self) -> dict:
        # return a dict with key = event.id, value = event.to_dict()
        return {event.id: event_to_dict(event) for event in self.state.history}

    def __str__(self) -> str:
        return f'ConversationMemory with {len(self.state.history)} total events'

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

    def update(self, state: State) -> None:
        """Update the conversation memory with new events."""

        # FIXME: this is a hack and doesn't work anyway
        if state.summary:
            # create a list of events using the summary, then from event id = end_id + 1 to the end of history
            summary_events = [
                event
                for event in state.history
                if event.id
                not in range(state.summary['start_id'], state.summary['end_id'] + 1)
            ]
            self.temporary_history = state.summary + summary_events
        else:
            self.temporary_history = state.history

        # the number of messages that are hidden from the user
        self.hidden_message_count = len(state.history) - len(self.temporary_history)

    def _has_summary(self) -> bool:
        """Check if the conversation has a summary."""
        return any(
            isinstance(event, AgentSummarizeAction) for event in self.state.history
        )

    def reset(self) -> None:
        # self.state.history = []
        pass
