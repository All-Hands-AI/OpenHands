from typing import ClassVar

from pydantic import StrictInt
from pydantic.dataclasses import dataclass

from opendevin.core.schema import ActionType

from .action import Action


@dataclass
class FileReadAction(Action):
    """
    Reads a file from a given path.
    Can be set to read specific lines using start and end
    Default lines 0:-1 (whole file)
    """

    path: str
    start: StrictInt = 0
    end: StrictInt = -1
    thought: str = ''
    action: str = ActionType.READ
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f'Reading file: {self.path}'


@dataclass
class FileWriteAction(Action):
    path: str
    content: str
    start: StrictInt = 0
    end: StrictInt = -1
    thought: str = ''
    action: str = ActionType.WRITE
    runnable: ClassVar[bool] = True

    @property
    def message(self) -> str:
        return f'Writing file: {self.path}'
