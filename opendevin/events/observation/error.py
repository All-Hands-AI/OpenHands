from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class ErrorObservation(Observation):
    """
    This data class represents an error encountered by the agent.
    """

    observation: ClassVar[str] = ObservationType.ERROR

    @property
    def message(self) -> str:
        return self.content
