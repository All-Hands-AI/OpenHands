from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class SuccessObservation(Observation):
    """
    This data class represents the result of a successful action.
    """

    observation: ClassVar[str] = ObservationType.SUCCESS

    @property
    def message(self) -> str:
        return self.content
