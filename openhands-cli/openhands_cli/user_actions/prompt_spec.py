from dataclasses import dataclass
from enum import Enum
from typing import Callable


class PromptType(Enum):
    """Types of prompts supported by the unified prompt system."""

    SELECTION = 'selection'  # Multiple choice with numbered options
    FREE_TEXT = 'free_text'  # Open text entry
    TEXT_WITH_AUTOCOMPLETE = 'text_with_autocomplete'  # Text input with suggestions


@dataclass
class ValidationRule:
    """A validation rule for prompt input."""

    validator: Callable[[str], bool]
    error_message: str


@dataclass
class PromptSpec:
    """Specification for a user prompt."""

    question: str
    prompt_type: PromptType
    options: list[str] | None = None
    default_value: str | None = None
    validation_rules: list[ValidationRule] | None = None
    escapable: bool = True
    step_info: str | None = None  # e.g., "(Step 1/3)"

    def get_formatted_question(self) -> str:
        """Get the question with optional step info prepended."""
        if self.step_info:
            return f'{self.step_info} {self.question}'
        return self.question
