from typing import ClassVar

from opendevin.core.schema import ObservationType

from .observation import Observation


class FileReadObservation(Observation):
    """
    This data class represents the content of a file.
    """

    path: str
    observation: ClassVar[str] = ObservationType.READ

    @property
    def message(self) -> str:
        return f'I read the file {self.path}.'


class FileWriteObservation(Observation):
    """
    This data class represents a file write operation
    """

    path: str
    observation: ClassVar[str] = ObservationType.WRITE

    @property
    def message(self) -> str:
        return f'I wrote to the file {self.path}.'
