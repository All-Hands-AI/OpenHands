from dataclasses import dataclass

from .base import Observation

@dataclass
class FileReadObservation(Observation):
    """
    This data class represents the content of a file.
    """

    path: str
    observation : str = "read"

    @property
    def message(self) -> str:
        return f"I read the file {self.path}."

@dataclass
class FileWriteObservation(Observation):
    """
    This data class represents a file write operation
    """

    path: str
    observation : str = "write"

    @property
    def message(self) -> str:
        return f"I wrote to the file {self.path}."


