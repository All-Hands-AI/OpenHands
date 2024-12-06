from dataclasses import dataclass

from openhands.events.observation.observation import Observation


@dataclass
class MessageObservation(Observation):
    """Observation for a message from the agent."""

    message: str

    def __str__(self) -> str:
        return self.message
