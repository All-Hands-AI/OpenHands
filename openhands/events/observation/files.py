from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class FileReadObservation(Observation):
    """This data class represents the content of a file."""

    path: str
    observation: str = ObservationType.READ

    @property
    def message(self) -> str:
        return f'I read the file {self.path}.'


@dataclass
class FileWriteObservation(Observation):
    """This data class represents a file write operation"""

    path: str
    observation: str = ObservationType.WRITE

    @property
    def message(self) -> str:
        return f'I wrote to the file {self.path}.'


@dataclass
class FileEditObservation(Observation):
    """This data class represents a file edit operation"""

    path: str
    prev_exist: bool
    observation: str = ObservationType.EDIT

    @property
    def message(self) -> str:
        return f'I edited the file {self.path}.'

    def __str__(self) -> str:
        ret = ''
        if self.prev_exist:
            ret += f'[Edited existing file {self.path}]\n'
        else:
            ret += f'[New file {self.path} is created.]\n'
        ret += '(begin of changes)\n'
        ret += self.content
        ret = ret.rstrip() + '\n'
        ret += '(end of changes)\n'
        return ret.rstrip() + '\n'
