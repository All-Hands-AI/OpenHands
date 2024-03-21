from abc import ABC, abstractmethod
from typing import List, Dict, Type
from dataclasses import dataclass
from enum import Enum

from .lib.event import Event
from .lib.command_manager import CommandManager
from .controller import AgentController

class Role(Enum):
    SYSTEM = "system"  # system message for LLM
    USER = "user"  # the user
    ASSISTANT = "assistant"  # the agent
    ENVIRONMENT = "environment"  # the environment (e.g., bash shell, web browser, etc.)

@dataclass
class Message:
    """
    This data class represents a message sent by an agent to another agent or user.
    """

    role: Role
    content: str
    # TODO: add more fields as needed

    def to_dict(self) -> Dict:
        """
        Converts the message to a dictionary (OpenAI chat-completion format).

        Returns:
        - message (Dict): A dictionary representation of the message.
        """
        role = self.role.value
        content = self.content
        if self.role == Role.ENVIRONMENT:
            content = f"Environment Observation:\n{content}"
            role = "user"  # treat environment messages as user messages
        return {"role": role, "content": content}


class Agent(ABC):
    """
    This abstract base class is an general interface for an agent dedicated to
    executing a specific instruction and allowing human interaction with the
    agent during execution.
    It tracks the execution status and maintains a history of interactions.

    :param instruction: The instruction for the agent to execute.
    :param workspace_dir: The working directory for the agent.
    :param model_name: The litellm name of the model to use for the agent.
    :param max_steps: The maximum number of steps to run the agent.
    """

    _registry: Dict[str, Type['Agent']] = {}

    def __init__(
        self,
        instruction: str,
        workspace_dir: str,
        model_name: str,
        max_steps: int = 100
    ):
        self.instruction = instruction
        self.workspace_dir = workspace_dir
        self.model_name = model_name
        self.max_steps = max_steps

        self._complete = False
        self._history: List[Message] = [Message(Role.USER, instruction)]

    @property
    def complete(self) -> bool:
        """
        Indicates whether the current instruction execution is complete.

        Returns:
        - complete (bool): True if execution is complete; False otherwise.
        """
        return self._complete

    @property
    def history(self) -> List[str]:
        """
        Provides the history of interactions or state changes since the instruction was initiated.

        Returns:
        - history (List[str]): A list of strings representing the history.
        """
        return self._history

    @abstractmethod
    def add_event(self, event: Event) -> None:
        """
        Adds an event to the agent's history.

        Parameters:
        - event (Event): The event to add to the history.
        """
        pass

    @abstractmethod
    def step(self, cmd_mgr: CommandManager) -> Event:
        """
        Starts the execution of the assigned instruction. This method should
        be implemented by subclasses to define the specific execution logic.
        """
        pass

    @abstractmethod
    def search_memory(self, query: str) -> List[str]:
        """
        Searches the agent's memory for information relevant to the given query.

        Parameters:
        - query (str): The query to search for in the agent's memory.

        Returns:
        - response (str): The response to the query.
        """
        pass

    def reset(self) -> None:
        """
        Resets the agent's execution status and clears the history. This method can be used
        to prepare the agent for restarting the instruction or cleaning up before destruction.

        """
        self.instruction = None
        self._complete = False
        self._history = []

    @classmethod
    def register(cls, name: str, agent_cls: Type['Agent']):
        """
        Registers an agent class in the registry.

        Parameters:
        - name (str): The name to register the class under.
        - agent_cls (Type['Agent']): The class to register.
        """
        if name in cls._registry:
            raise ValueError(f"Agent class already registered under '{name}'.")
        cls._registry[name] = agent_cls

    @classmethod
    def get_cls(cls, name: str) -> Type['Agent']:
        """
        Retrieves an agent class from the registry.

        Parameters:
        - name (str): The name of the class to retrieve

        Returns:
        - agent_cls (Type['Agent']): The class registered under the specified name.
        """
        if name not in cls._registry:
            raise ValueError(f"No agent class registered under '{name}'.")
        return cls._registry[name]
