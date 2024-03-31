from dataclasses import dataclass

from .base import Observation

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



