from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

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


class ThoughtsMixin:
    """Mixin to handle backward compatibility for thought field assignment."""

    def __setattr__(self, name: str, value: Any) -> None:
        if name == 'thought' and isinstance(value, str):
            # Import here to avoid circular imports
            from openhands.events.action.thoughts import ThoughtsDict

            # Convert string assignment to ThoughtsDict
            if hasattr(self, 'thought') and isinstance(
                getattr(self, 'thought'), ThoughtsDict
            ):
                getattr(self, 'thought').set_default(value)
                return
            else:
                value = ThoughtsDict(value)
        super().__setattr__(name, value)


@dataclass
class Action(ThoughtsMixin, Event):
    runnable: ClassVar[bool] = False
