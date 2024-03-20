from abc import ABC, abstractmethod
from typing import List, Dict, Type
from dataclasses import dataclass
from enum import Enum


class Role(Enum):
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


class Agent(ABC):
    """
    This abstract base class is an general interface for an agent dedicated to
    executing a specific instruction and allowing human interaction with the
    agent during execution.
    It tracks the execution status and maintains a history of interactions.
    """

    _registry: Dict[str, Type['Agent']] = {}

    def __init__(
        self,
        instruction: str,
        max_steps: int = 100
    ):
        self.instruction = instruction
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
    def run(self) -> None:
        """
        Starts the execution of the assigned instruction. This method should
        be implemented by subclasses to define the specific execution logic.
        """
        pass

    @abstractmethod
    def chat(self, message: str) -> None:
        """
        Optional method for interactive communication with the agent during its execution. Implementations
        can use this method to modify the agent's behavior or state based on chat inputs.

        Parameters:
        - message (str): The chat message or command.
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
    def create_instance(cls, name: str, instruction: str) -> 'Agent':
        """
        Creates an instance of a registered agent class based on the given name.

        Parameters:
        - name (str): The name of the agent class to instantiate.
        - instruction (str): The instruction for the new agent instance.

        Returns:
        - An instance of the specified agent class.
        """
        if name not in cls._registry:
            raise ValueError(f"No agent class registered under '{name}'.")
        agent_cls = cls._registry[name]
        return agent_cls(instruction)
