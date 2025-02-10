from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from openhands.events.event import Event


class ActionConfirmationStatus(str, Enum):
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    AWAITING_CONFIRMATION = 'awaiting_confirmation'


class ActionSecurityRisk(int, Enum):
    UNKNOWN = -1
    LOW = 0
    MEDIUM = 1
    HIGH = 2


@dataclass
class Action(Event):
    runnable: ClassVar[bool] = False

@dataclass
class FileEditAction(Action):
    runnable: ClassVar[bool] = True
    path: str
    command: str
    file_text: str = None
    old_str: str = None
    new_str: str = None
    insert_line: int = None
    view_range: list[int] = None
    content: str = None
    start: int = None
    end: int = None
