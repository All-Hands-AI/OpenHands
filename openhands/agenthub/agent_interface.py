from abc import ABC, abstractmethod  # Import ABC and abstractmethod
from typing import Any, Dict, List, Optional, TypedDict

from openhands.controller.state.state import State
from openhands.core.message import Message
from openhands.events.event import Event
from openhands.llm.llm import LLM  # Import the LLM class


class LLMCompletionParams(TypedDict, total=False):
    """TypedDict for LLM completion parameters."""

    messages: List[Message]
    tools: Optional[List[Any]]
    extra_body: Optional[Dict[str, Any]]
    extra: Optional[Dict[str, Any]]


class LLMCompletionProvider(ABC):
    """Mixin interface for agents that can expose their LLM call generation details.

    This interface is used by condensers that need to use the agent's LLM completion
    parameters to ensure consistent caching between the agent and condenser.
    """

    llm: LLM  # Property to hold the LLM instance

    @abstractmethod
    def _get_messages(self, events: list[Event]) -> list[Message]:
        """Convert events to messages for the LLM."""
        pass

    @abstractmethod
    def build_llm_completion_params(
        self, events: List[Event], state: State
    ) -> dict[str, Any]:
        """Build parameters for LLM completion.

        Args:
            events: List of events to convert to messages for the LLM
            state: Current state

        Returns:
            Dictionary of parameters for LLM completion
        """
        pass
