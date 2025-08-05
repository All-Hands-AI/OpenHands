from dataclasses import dataclass, field
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
    # Add reasoning_content as a field with init=False so it doesn't affect parameter order
    # This field will be used to store the reasoning content from the LLM
    reasoning_content: str | None = field(default=None, init=False)
    
    def __post_init__(self):
        # Initialize reasoning_content if not already set
        if not hasattr(self, 'reasoning_content'):
            self.reasoning_content = None
