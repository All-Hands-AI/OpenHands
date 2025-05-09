from enum import Enum
from typing import Any, cast

from termcolor import colored


class TermColor(Enum):
    """Terminal color codes."""

    WARNING = 'yellow'
    SUCCESS = 'green'
    ERROR = 'red'
    INFO = 'blue'


def colorize(text: str, color: TermColor = TermColor.WARNING) -> str:
    """Colorize text with specified color.

    Args:
        text (str): Text to be colored
        color (TermColor, optional): Color to use. Defaults to TermColor.WARNING

    Returns:
        str: Colored text
    """
    # The colored function returns Any in mypy's view, so we need to cast it
    result: Any = colored(text, color.value)
    return cast(str, result)
