from dataclasses import dataclass

from opendevin.schema import ObservationType

from .base import Observation


@dataclass
class ErrorObservation(Observation):
    """
    This data class represents an error encountered by the agent.
    """

    observation: str = ObservationType.ERROR

    @property
    def message(self) -> str:
        return self.content
