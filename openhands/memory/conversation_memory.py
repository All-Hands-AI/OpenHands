from enum import Enum

from openhands.controller.state.state import State
from openhands.core.config.llm_config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.agent import AgentSummarizeAction
from openhands.events.event import Event
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM
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
        # total messages in the conversation
        self.total_message_count = 0

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
        return self.long_term_memory.text_search(query, count, start)

    def recall_memory(
        self, llm: LLM, query: str, top_k: int = 5
    ) -> list[Event]:
        """
        Get the most similar events based on the query.

        Args:
            query: The query string for semantic search.
            top_k: Number of top results to retrieve.

        Returns:
            A list of semantically similar events.
        """
        # get the most similar events based on the query
        # for testing recall with litellm
        return llm.search(query, self.state.history, top_k)

    def update(self, state: State) -> None:
        """Update the conversation memory with information from the new events."""

        # the number of messages that are hidden from the user
        # is the number of events in summary
        if state.summary:
            self.hidden_message_count = state.summary.end_id - state.summary.start_id

    def _has_summary(self) -> bool:
        """Check if the conversation has a summary."""
        return any(
            isinstance(event, AgentSummarizeAction) for event in self.state.history
        )

    def reset(self) -> None:
        # self.state.history = []
        pass
