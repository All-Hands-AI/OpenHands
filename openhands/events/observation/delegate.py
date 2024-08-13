from dataclasses import dataclass

from openhands.core.schema import ObservationType

from .observation import Observation


@dataclass
class AgentDelegateObservation(Observation):
    """This data class represents the result from delegating to another agent"""

    outputs: dict
    observation: str = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return ''
