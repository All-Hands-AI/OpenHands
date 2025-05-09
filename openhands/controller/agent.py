from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from openhands.controller.state.state import State
    from openhands.core.config import AgentConfig
    from openhands.events.action import Action
from openhands.a2a.A2AManager import A2AManager
from openhands.core.exceptions import (
    AgentAlreadyRegisteredError,
    AgentNotRegisteredError,
)
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
        workspace_mount_path_in_sandbox_store_in_session: bool = True,
        a2a_manager: A2AManager | None = None,
        **kwargs,
    ):
        self.llm = llm
        self.config = config
        self._complete = False
        self.prompt_manager: 'PromptManager' | None = None
        self.mcp_tools: list[dict] = []
        self.search_tools: list[dict] = []
        self.workspace_mount_path_in_sandbox_store_in_session = (
            workspace_mount_path_in_sandbox_store_in_session
        )
        self.a2a_manager = a2a_manager
        self.system_prompt: str = ''
        self.user_prompt: str = ''
        self.knowledge_base: dict[str, dict] = {}

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

    def set_search_tools(self, search_tools: list[dict]) -> None:
        """Sets the list of search tools for the agent.

        Args:
        - search_tools (list[dict]): The list of search tools.
        """
        self.search_tools = search_tools

    def set_system_prompt(self, system_prompt: str) -> None:
        """Set the system prompt for the agent.

        Args:
        - system_prompt (str): The system prompt.
        """
        self.system_prompt = system_prompt

    def set_user_prompt(self, user_prompt: str) -> None:
        """Set the user prompt for the agent.

        Args:
        - user_prompt (str): The user prompt.
        """
        self.user_prompt = user_prompt

    def update_agent_knowledge_base(
        self, knowledge_base: list[dict] | None = None
    ) -> None:
        """Update the knowledge base for the agent.

        Args:
        - knowledge_base (list[dict]): The knowledge base.
        """
        print(f'Update agent knowledge base: {knowledge_base}')
        # update
        if knowledge_base:
            for k in knowledge_base:
                if k.get('chunkId', None):
                    self.knowledge_base[k['chunkId']] = k
