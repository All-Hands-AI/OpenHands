from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Type

from openhands.llm.streaming_llm import StreamingLLM

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
        from openhands.events.stream import EventStream

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
        self.knowledge_base: dict[str, Any] = {}
        self.event_stream: 'EventStream' | None = None
        self.session_id: str | None = kwargs.get('session_id', None)
        self.enable_streaming: bool = kwargs.get('enable_streaming', False)
        self.streaming_llm: StreamingLLM | None = None
        self.output_config: dict | None = kwargs.get('output_config', None)
        self.space_id: int | None = None
        self.thread_follow_up: int | None = None

    @property
    def complete(self) -> bool:
        """Indicates whether the current instruction execution is complete.

        Returns:
        - complete (bool): True if execution is complete; False otherwise.
        """
        return self._complete

    @abstractmethod
    def step(self, state: 'State') -> Optional['Action']:
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

    def set_output_config(self, output_config: dict) -> None:
        """Set the output config for the agent.

        Args:
        - output_config (dict): The output config.
        """
        self.output_config = output_config

    def update_agent_knowledge_base(self, knowledge_base: Any | None = None) -> dict:
        """Update the knowledge base for the agent and return new items.

        Args:
            knowledge_base (Any | None): The new knowledge base to update

        Returns:
            dict: Object with structure similar to self.knowledge_base but only containing new items
        """
        # Initialize structure
        if 'knowledge_base_results' not in self.knowledge_base:
            self.knowledge_base['knowledge_base_results'] = {}
        if 'x_results' not in self.knowledge_base:
            self.knowledge_base['x_results'] = {}

        if not knowledge_base:
            return {'knowledge_base_results': {}, 'x_results': {}}

        new_items: dict[str, Any] = {'knowledge_base_results': {}, 'x_results': {}}

        # Update knowledge_base_results and collect new items
        if 'knowledge_base_results' in knowledge_base:
            for item in knowledge_base['knowledge_base_results']:
                chunk_id = item.get('chunkId')
                if chunk_id:
                    # Check if it's new before updating
                    if chunk_id not in self.knowledge_base['knowledge_base_results']:
                        new_items['knowledge_base_results'][chunk_id] = item
                    # Update the knowledge base
                    self.knowledge_base['knowledge_base_results'][chunk_id] = item

        # Update x_results and collect new items
        if 'x_results' in knowledge_base:
            for item in knowledge_base['x_results']:
                chunk_id = item.get('chunkId')
                if chunk_id:
                    # Check if it's new before updating
                    if chunk_id not in self.knowledge_base['x_results']:
                        new_items['x_results'][chunk_id] = item
                    # Update the knowledge base
                    self.knowledge_base['x_results'][chunk_id] = item

        return new_items

    def check_has_knowledge_base(self):
        return self.knowledge_base and (
            'knowledge_base_results' in self.knowledge_base
            or 'x_results' in self.knowledge_base
        )

    def set_event_stream(self, event_stream) -> None:
        self.event_stream = event_stream

    def set_space_id(self, space_id: int) -> None:
        self.space_id = space_id

    def set_thread_follow_up(self, thread_follow_up: int) -> None:
        self.thread_follow_up = thread_follow_up
