from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from openhands.controller.state.state import State
    from openhands.core.config import AgentConfig
    from openhands.events.action import Action
    from openhands.events.action.message import SystemMessageAction
from openhands.core.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotRegisteredError,
)
from openhands.events.event import EventSource
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

    _registry: dict[str, Type['Agent']] = {}
    sandbox_plugins: list[PluginRequirement] = []

    def __init__(
        self,
        llm: LLM,
        config: 'AgentConfig',
    ):
        self.llm = llm
        self.config = config
        self._complete = False
        self.prompt_manager: 'PromptManager' | None = None
        self.mcp_tools: list[dict] = []
        self.tools: list = []
        
    def get_initial_message(self) -> 'SystemMessageAction':
        """
        Returns a SystemMessageAction containing the system message and tools.
        This will be added to the event stream as the first message.
        
        Returns:
            SystemMessageAction: The system message action with content and tools
        """
        from openhands.events.action.message import SystemMessageAction
        
        if self.prompt_manager is None:
            raise ValueError("Agent's prompt_manager is not initialized")
            
        system_message = self.prompt_manager.get_system_message()
        system_message_action = SystemMessageAction(
            content=system_message,
            tools=self.tools
        )
        system_message_action._source = EventSource.AGENT
        
        return system_message_action

    @property
    def complete(self) -> bool:
        """Indicates whether the current instruction execution is complete.

        Returns:
        - complete (bool): True if execution is complete; False otherwise.
        """
        return self._complete

    @abstractmethod
    def step(self, state: 'State') -> 'Action':
        """Starts the execution of the assigned instruction. This method should
        be implemented by subclasses to define the specific execution logic.
        """
        pass

    def reset(self) -> None:
        """Resets the agent's execution status and clears the history. This method can be used
        to prepare the agent for restarting the instruction or cleaning up before destruction.

        """
        # TODO clear history
        self._complete = False

        if self.llm:
            self.llm.reset()

    @property
    def name(self):
        return self.__class__.__name__

    @classmethod
    def register(cls, name: str, agent_cls: Type['Agent']):
        """Registers an agent class in the registry.

        Parameters:
        - name (str): The name to register the class under.
        - agent_cls (Type['Agent']): The class to register.

        Raises:
        - AgentAlreadyRegisteredError: If name already registered
        """
        if name in cls._registry:
            raise AgentAlreadyRegisteredError(name)
        cls._registry[name] = agent_cls

    @classmethod
    def get_cls(cls, name: str) -> Type['Agent']:
        """Retrieves an agent class from the registry.

        Parameters:
        - name (str): The name of the class to retrieve

        Returns:
        - agent_cls (Type['Agent']): The class registered under the specified name.

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
        - mcp_tools (list[dict]): The list of MCP tools.
        """
        self.mcp_tools = mcp_tools

    def get_initial_message(self) -> 'SystemMessageAction':
        """Returns the initial system message for the agent.

        This message includes the system prompt and available tools.
        It should be the first message in the event stream.

        Returns:
            SystemMessageAction: The system message action with prompt and tools
        """
        from openhands.events.action.message import SystemMessageAction

        if not self.prompt_manager:
            raise ValueError(
                'Prompt manager must be initialized before getting initial message'
            )

        system_message = self.prompt_manager.get_system_message()

        # Get tools if available
        tools = getattr(self, 'tools', None)

        system_message_action = SystemMessageAction(content=system_message, tools=tools)
        # Set the source attribute
        system_message_action._source = EventSource.AGENT  # type: ignore

        return system_message_action
