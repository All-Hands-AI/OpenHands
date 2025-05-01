from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypedDict

from openhands.controller.state.state import State
from openhands.core.message import Message
from openhands.events.action.message import MessageAction

if TYPE_CHECKING:
    from openhands.core.config import AgentConfig
    from openhands.events.action import Action
    from openhands.events.action.message import SystemMessageAction
from openhands.core.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotRegisteredError,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.llm.llm import LLM
from openhands.runtime.plugins import PluginRequirement

if TYPE_CHECKING:
    from openhands.utils.prompt import PromptManager


class Agent(ABC):
    DEPRECATED = False
    """
    This abstract base class is an general interface for an agent dedicated to
    executing a specific instruction and allowing human interaction with the
    agent during execution.
    It tracks the execution status and maintains a history of interactions.
    """

    _registry: dict[str, type['Agent']] = {}
    sandbox_plugins: list[PluginRequirement] = []

    def __init__(
        self,
        llm: LLM,
        config: 'AgentConfig',
    ):
        self.llm = llm
        self.config = config
        self._complete = False
        self.prompt_manager: 'PromptManager | None' = None
        self.mcp_tools: list[dict] = []
        self.tools: list = []

    def get_system_message(self) -> 'SystemMessageAction | None':
        """Returns a SystemMessageAction containing the system message and tools.

        This will be added to the event stream as the first message.

        Returns:
            SystemMessageAction: The system message action with content and tools
            None: If there was an error generating the system message
        """
        # Import here to avoid circular imports
        from openhands.events.action.message import SystemMessageAction

        try:
            if not self.prompt_manager:
                logger.warning(
                    f'[{self.name}] Prompt manager not initialized before getting system message'
                )
                return None

            system_message = self.prompt_manager.get_system_message()

            # Get tools if available
            tools = getattr(self, 'tools', None)

            system_message_action = SystemMessageAction(
                content=system_message, tools=tools, agent_class=self.name
            )
            # Set the source attribute
            system_message_action._source = EventSource.AGENT  # type: ignore

            return system_message_action
        except Exception as e:
            logger.warning(f'[{self.name}] Failed to generate system message: {e}')
            return None

    @property
    def complete(self) -> bool:
        """Indicates whether the current instruction execution is complete.

        Returns:
        - complete (bool): True if execution is complete; False otherwise.
        """
        return self._complete

    @abstractmethod
    def step(self, state: 'State') -> 'Action':
        """Starts the execution of the assigned instruction.

        This method should be implemented by subclasses to define the specific execution logic.
        """
        pass

    def reset(self) -> None:
        """Resets the agent's execution status and clears the history.

        This method can be used to prepare the agent for restarting the instruction or cleaning up before destruction.
        """
        # TODO clear history
        self._complete = False

        if self.llm:
            self.llm.reset()

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @classmethod
    def register(cls, name: str, agent_cls: type['Agent']) -> None:
        """Registers an agent class in the registry.

        Parameters:
        - name (str): The name to register the class under.
        - agent_cls (type['Agent']): The class to register.

        Raises:
        - AgentAlreadyRegisteredError: If name already registered
        """
        if name in cls._registry:
            raise AgentAlreadyRegisteredError(name)
        cls._registry[name] = agent_cls

    @classmethod
    def get_cls(cls, name: str) -> type['Agent']:
        """Retrieves an agent class from the registry.

        Parameters:
        - name (str): The name of the class to retrieve

        Returns:
        - agent_cls (type['Agent']): The class registered under the specified name.

        Raises:
        - AgentNotRegisteredError: If name not registered
        """
        if name not in cls._registry:
            raise AgentNotRegisteredError(name)
        return cls._registry[name]

    @classmethod
    def list_agents(cls) -> list[str]:
        """Retrieves the list of all agent names from the registry.

        Raises:
        - AgentNotRegisteredError: If no agent is registered
        """
        if not bool(cls._registry):
            raise AgentNotRegisteredError()
        return list(cls._registry.keys())

    def set_mcp_tools(self, mcp_tools: list[dict]) -> None:
        """Sets the list of MCP tools for the agent.

        Args:
            mcp_tools: The list of MCP tools.
        """
        self.mcp_tools = mcp_tools


class LLMCompletionParams(TypedDict, total=False):
    messages: list[Message]
    tools: list[Any] | None
    extra_body: dict[str, Any] | None
    extra: dict[str, Any] | None


class LLMCompletionProvider(ABC):
    """Mixin interface for agents that can expose their LLM call generation details.

    This interface is used by condensers that need to use the agent's LLM completion
    parameters to ensure consistent caching between the agent and condenser.
    """

    llm: LLM

    @abstractmethod
    def get_messages(
        self, condensed_history: list[Event], initial_user_message: MessageAction
    ) -> list[Message]:
        """Convert events to messages for the LLM."""
        pass

    @abstractmethod
    def build_llm_completion_params(
        self, condensed_history: list[Event], state: State
    ) -> dict[str, Any]:
        """Build parameters for LLM completion.

        Args:
            condensed_history: list of events to convert to messages for the LLM
            state: Current state

        Returns:
            dict of parameters for LLM completion
        """
        pass

    def _get_initial_user_message(self, history: list[Event]) -> MessageAction:
        """Finds the initial user message action from the full history."""
        initial_user_message: MessageAction | None = None
        for event in history:
            if isinstance(event, MessageAction) and event.source == 'user':
                initial_user_message = event
                break

        if initial_user_message is None:
            # This should not happen in a valid conversation
            logger.error(
                f'CRITICAL: Could not find the initial user MessageAction in the full {len(history)} events history.'
            )
            # Depending on desired robustness, could raise error or create a dummy action
            # and log the error
            raise ValueError(
                'Initial user message not found in history. Please report this issue.'
            )
        return initial_user_message
