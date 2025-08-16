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
class Thought:
    """Container for agent reasoning.

    Attributes:
        text: The visible plain thought string used throughout the UI/logs.
        reasoning_content: Optional provider-native reasoning content (e.g., LiteLLM reasoning).
    """

    text: str = ''
    reasoning_content: str | None = None

    def __bool__(self) -> bool:
        return bool(self.text or self.reasoning_content)

    def __str__(self) -> str:
        return self.text
