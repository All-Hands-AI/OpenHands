"""Gemini-style file editor actions."""

from typing import Any, Optional

from openhands.events.action.action import Action
from openhands.llm.tool_names import (
    GEMINI_EDIT_TOOL_NAME,
    GEMINI_READ_FILE_TOOL_NAME,
    GEMINI_WRITE_FILE_TOOL_NAME,
)


class GeminiEditAction(Action):
    """Action for Gemini-style edit operations."""
    
    action = GEMINI_EDIT_TOOL_NAME

    def __init__(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        expected_replacements: int = 1,
    ):
        """Initialize a GeminiEditAction.

        Args:
            file_path: The absolute path to the file to modify.
            old_string: The exact string to replace.
            new_string: The string to replace old_string with.
            expected_replacements: The expected number of replacements.
        """
        self.file_path = file_path
        self.old_string = old_string
        self.new_string = new_string
        self.expected_replacements = expected_replacements

    def to_dict(self) -> dict:
        """Convert the action to a dictionary."""
        return {
            'action': self.action,
            'file_path': self.file_path,
            'old_string': self.old_string,
            'new_string': self.new_string,
            'expected_replacements': self.expected_replacements,
        }


class GeminiWriteFileAction(Action):
    """Action for Gemini-style write file operations."""
    
    action = GEMINI_WRITE_FILE_TOOL_NAME

    def __init__(self, file_path: str, content: str):
        """Initialize a GeminiWriteFileAction.

        Args:
            file_path: The absolute path to the file to write to.
            content: The content to write to the file.
        """
        self.file_path = file_path
        self.content = content

    def to_dict(self) -> dict:
        """Convert the action to a dictionary."""
        return {
            'action': self.action,
            'file_path': self.file_path,
            'content': self.content,
        }


class GeminiReadFileAction(Action):
    """Action for Gemini-style read file operations."""
    
    action = GEMINI_READ_FILE_TOOL_NAME

    def __init__(
        self,
        absolute_path: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """Initialize a GeminiReadFileAction.

        Args:
            absolute_path: The absolute path to the file to read.
            offset: The offset to start reading from.
            limit: The maximum number of characters to read.
        """
        self.absolute_path = absolute_path
        self.offset = offset
        self.limit = limit

    def to_dict(self) -> dict[str, Any]:
        """Convert the action to a dictionary."""
        result: dict[str, Any] = {
            'action': self.action,
            'absolute_path': self.absolute_path,
        }
        if self.offset is not None:
            result['offset'] = self.offset
        if self.limit is not None:
            result['limit'] = self.limit
        return result