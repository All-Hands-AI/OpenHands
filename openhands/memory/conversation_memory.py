from enum import Enum

from openhands.controller.state.state import State
from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM
from openhands.memory.base_memory import Memory


class StorageType(Enum):
    IN_MEMORY = 'in-memory'
    VECTOR = 'vector'


class ConversationMemory(Memory):
    """Allows the agent to recall events from its entire history, with support for summarization and recall.

    This class handles the summarized events (from state.summary['start_id] to state.summary['end_id'])
    and slices the history to include only the events after the summary.
    """

    memory: list[Event]
    memory_config: LLMConfig

    def __init__(
        self,
        memory_config: LLMConfig,
        state: State,
    ) -> None:
        """
        Initialize ConversationMemory with a reference to history and long-term memory.

        Args:
        - history: The history of the current agent conversation.
        - llm_config: The LLM configuration.
        - top_k: Number of top results to retrieve.
        """
        self.memory = []
        self.memory_config = memory_config
        # total messages in the conversation
        # won't this always be the same as len(history)?
        # core memory isn't counted here
        self.total_message_count = 0
        # of which hidden
        self.hidden_message_count = 0

        # init storage type
        self.storage_type = StorageType.IN_MEMORY

        # read itself from the runtime state
        self.update(state)

    def update(self, state: State) -> None:
        """Updates the conversation memory from a new runtime state."""
        # this isn't actually state.history
        # if it has a summary, the messages from summary.start_id to summary.end_id are not included,
        # but replaced with a single summary event
        if state and state.summary:
            self.memory = (
                state.history[: state.summary.start_id]
                + [state.summary]
                + state.history[state.summary.end_id :]
            )
            self.hidden_message_count = state.summary.end_id - state.summary.start_id
        else:
            self.memory = state.history  # this is not cool but let it be for now
            self.hidden_message_count = 0

    def reset(self) -> None:
        """Resets the conversation memory."""
        self.memory = []
        self.total_message_count = 0
        self.hidden_message_count = 0

    def update_summary(self, summary: str, hidden_count: int) -> None:
        """Updates the memory with a new summary and tracks hidden messages."""
        self.hidden_message_count = hidden_count

    def to_dict(self) -> dict:
        # return a dict with key = event.id, value = event.to_dict()
        return {event.id: event_to_dict(event) for event in self.memory}

    def __str__(self) -> str:
        return f'ConversationMemory with {len(self.memory)} total events'

    def search(self, llm: LLM, query: str, top_k: int = 5) -> list:
        """Searches the conversation memory for relevant messages."""
        if not self.memory or not query:
            return []

        if self.storage_type == StorageType.IN_MEMORY:
            # use the llm.py search to find relevant messages
            recalled_events = llm.search(query=query, history=self.memory, top_k=top_k)
        else:
            raise ValueError(f'Unsupported storage type: {self.storage_type}')

        return recalled_events

    def recall_memory(
        self, llm: LLM, state: State, query: str, top_k: int = 5
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
        return llm.search(query, state.history, top_k)
