from dataclasses import dataclass

from .base import Observation
from opendevin.schema import ObservationType


@dataclass
class AgentDelegateObservation(Observation):
    """
    This data class represents a delegate observation.
    This is used when the produced action is NOT executable.
    """

    observation: str = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return ''
