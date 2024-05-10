from dataclasses import dataclass
from typing import ClassVar

from opendevin.events.event import Event


@dataclass
class Action(Event):
    runnable: ClassVar[bool] = False
