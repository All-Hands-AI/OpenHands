from typing import List
from dataclasses import dataclass

@dataclass
class Observation:
    """
    This data class represents an observation of the environment.
    """
    content: str

    def __str__(self) -> str:
        return self.content

    def to_dict(self) -> dict:
        """Converts the observation to a dictionary."""
        return {
            "observation_type": self.__class__.__name__,
            "args": self.__dict__
        }

@dataclass
class CmdOutputObservation(Observation):
    """
    This data class represents the output of a command.
    """
    command_id: int
    command: str
    exit_code: int = 0
    
    @property
    def error(self) -> bool:
        return self.exit_code != 0

@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """
    url: str

@dataclass
class UserMessageObservation(Observation):
    """
    This data class represents a message sent by the user.
    """
    role: str = "user"

@dataclass
class AgentMessageObservation(Observation):
    """
    This data class represents a message sent by the agent.
    """
    role: str = "assistant"

@dataclass
class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """
    memories: List[str]
    role: str = "assistant"
    
