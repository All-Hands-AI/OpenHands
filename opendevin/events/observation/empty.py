from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class NullObservation(Observation):
    """
    This data class represents a null observation.
    This is used when the produced action is NOT executable.
    """

    observation: ClassVar[str] = ObservationType.NULL

    @property
    def message(self) -> str:
        return 'No observation'
