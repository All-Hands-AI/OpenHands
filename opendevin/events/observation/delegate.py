from dataclasses import dataclass

from opendevin.schema import ObservationType

from .observation import Observation


@dataclass
class AgentDelegateObservation(Observation):
    """
    This data class represents a delegate observation.
    This is used when the produced action is NOT executable.
    """

    outputs: dict
    observation: str = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return ''
