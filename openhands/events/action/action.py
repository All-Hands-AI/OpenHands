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

    def __post_init__(self):
        # Normalize thought attribute across all actions for backward compatibility
        # Only coerce at construction time; internal components should assume Thought is present thereafter
        try:
            t = getattr(self, 'thought')
        except AttributeError:
            return
        from openhands.events.action.action import (
            Thought as _Thought,  # local import to avoid circular issues
        )

        if isinstance(t, str):
            setattr(self, 'thought', _Thought(text=t))
        elif t is None:
            setattr(self, 'thought', _Thought())
        elif not isinstance(t, _Thought):
            setattr(self, 'thought', _Thought(text=str(t)))


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
        # Concatenate provider-native reasoning content and visible text for display.
        # Do not rely on this for content sent to the LLM; conversation_memory must use .text only.
        if self.reasoning_content and self.text:
            return f'{self.reasoning_content}\n\n{self.text}'
        if self.reasoning_content:
            return self.reasoning_content
        return self.text

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        # Allow comparing Thought to plain strings for backward compatibility in tests/UI code
        if isinstance(other, Thought):
            return (
                self.text == other.text
                and self.reasoning_content == other.reasoning_content
            )
        if isinstance(other, str):
            return self.text == other
        return NotImplemented  # type: ignore[return-value]
