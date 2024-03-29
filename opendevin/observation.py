import copy
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
        extras = copy.deepcopy(self.__dict__)
        extras.pop("content", None)
        observation = "observation"
        if hasattr(self, "observation"):
            observation = self.observation
        return {
            "observation": observation,
            "content": self.content,
            "extras": extras,
            "message": self.message,
        }

    @property
    def message(self) -> str:
        """Returns a message describing the observation."""
        return ""


@dataclass
class CmdOutputObservation(Observation):
    """
    This data class represents the output of a command.
    """

    command_id: int
    command: str
    exit_code: int = 0
    observation : str = "run"

    @property
    def error(self) -> bool:
        return self.exit_code != 0

    @property
    def message(self) -> str:
        return f'Command `{self.command}` executed with exit code {self.exit_code}.'

@dataclass
class FileReadObservation(Observation):
    """
    This data class represents the content of a file.
    """

    path: str
    observation : str = "read"

    @property
    def message(self) -> str:
        return f"I read the file {self.path}."

@dataclass
class FileWriteObservation(Observation):
    """
    This data class represents a file write operation
    """

    path: str
    observation : str = "write"

    @property
    def message(self) -> str:
        return f"I wrote to the file {self.path}."

@dataclass
class BrowserOutputObservation(Observation):
    """
    This data class represents the output of a browser.
    """

    url: str
    status_code: int = 200
    error: bool = False
    observation : str = "browse"

    @property
    def message(self) -> str:
        return "Visited " + self.url


@dataclass
class UserMessageObservation(Observation):
    """
    This data class represents a message sent by the user.
    """

    role: str = "user"
    observation : str = "message"

    @property
    def message(self) -> str:
        return ""


@dataclass
class AgentMessageObservation(Observation):
    """
    This data class represents a message sent by the agent.
    """

    role: str = "assistant"
    observation : str = "message"

    @property
    def message(self) -> str:
        return ""


@dataclass
class AgentRecallObservation(Observation):
    """
    This data class represents a list of memories recalled by the agent.
    """

    memories: List[str]
    role: str = "assistant"
    observation : str = "recall"

    @property
    def message(self) -> str:
        return "The agent recalled memories."


@dataclass
class AgentErrorObservation(Observation):
    """
    This data class represents an error encountered by the agent.
    """
    observation : str = "error"

    @property
    def message(self) -> str:
        return "Oops. Something went wrong: " + self.content

@dataclass
class NullObservation(Observation):
    """
    This data class represents a null observation.
    This is used when the produced action is NOT executable.
    """
    observation : str = "null"

    @property
    def message(self) -> str:
        return ""
