from dataclasses import dataclass

from .base import Observation

@dataclass
class AgentErrorObservation(Observation):
    """
    This data class represents an error encountered by the agent.
    """
    observation : str = "error"

    @property
    def message(self) -> str:
        return "Oops. Something went wrong: " + self.content


