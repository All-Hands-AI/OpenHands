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
        return self.__dict__

@dataclass
class CmdOutputObservation(Observation):
    """
    This data class represents the output of a command.
    """
    command_id: int
    command: str


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
