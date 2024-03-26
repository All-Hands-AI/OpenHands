from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from opendevin.action import Action
    from opendevin.state import State
from opendevin.llm.llm import LLM

class Agent(ABC):
    """
    Abstract base class for an agent that executes specific instructions and
    allows human interaction during execution. It tracks execution status and
    maintains a history of interactions.

    Attributes:
        instruction (str): The current instruction for the agent to execute.
        llm (LLM): The language model used by the agent.
        _complete (bool): Flag indicating if the instruction execution is complete.

    Class Attributes:
        _registry (Dict[str, Type["Agent"]]): Registry mapping agent names to their classes.
    """

    _registry: Dict[str, Type["Agent"]] = {}

    def __init__(self, llm: LLM) -> None:
        """
        Initializes the agent with a language model.

        Parameters:
            llm (LLM): The language model to use for the agent.
        """
        self.instruction: str = ""
        self.llm: LLM = llm
        self._complete: bool = False

    @property
    def complete(self) -> bool:
        """
        Indicates whether the current instruction execution is complete.

        Returns:
            bool: True if execution is complete, False otherwise.
        """
        return self._complete

    @abstractmethod
    def step(self, state: "State") -> "Action":
        """
        Executes a step of the assigned instruction.

        Parameters:
            state (State): The current state of the environment.

        Returns:
            Action: The action to be taken based on the current state.
        """
        pass

    @abstractmethod
    def search_memory(self, query: str) -> List[str]:
        """
        Searches the agent's memory for information relevant to the query.

        Parameters:
            query (str): The query to search for in the agent's memory.

        Returns:
            List[str]: Responses to the query.
        """
        pass

    def reset(self) -> None:
        """
        Resets the agent's execution status and clears the history.
        """
        self.instruction = ""
        self._complete = False

    @classmethod
    def register(cls, name: str, agent_cls: Type["Agent"]) -> None:
        """
        Registers an agent class in the registry.

        Parameters:
            name (str): The name to register the class under.
            agent_cls (Type[Agent]): The class to register.

        Raises:
            ValueError: If a class is already registered under the given name.
        """
        if name in cls._registry:
            raise ValueError(f"Agent class already registered under '{name}'.")
        cls._registry[name] = agent_cls

    @classmethod
    def get_cls(cls, name: str) -> Optional[Type["Agent"]]:
        """
        Retrieves an agent class from the registry by name.

        Parameters:
            name (str): The name of the class to retrieve.

        Returns:
            Optional[Type[Agent]]: The class registered under the specified name or None if not found.
        """
        return cls._registry.get(name, None)
