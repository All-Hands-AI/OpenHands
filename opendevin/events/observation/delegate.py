from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class AgentDelegateObservation(Observation):
    """
    This data class represents the result from delegating to another agent
    """

    outputs: dict
    observation: ClassVar[str] = ObservationType.DELEGATE

    @property
    def message(self) -> str:
        return ''
