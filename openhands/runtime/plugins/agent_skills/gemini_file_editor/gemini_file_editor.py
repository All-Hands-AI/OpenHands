"""Gemini-style file editor implementation for OpenHands."""

import os
from typing import Any, Optional, Union

from openhands_aci.utils.diff import get_diff  # type: ignore

from openhands.events.action import Action
from openhands.events.action.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.llm.tool_names import (
    GEMINI_EDIT_TOOL_NAME,
    GEMINI_READ_FILE_TOOL_NAME,
    GEMINI_WRITE_FILE_TOOL_NAME,
)
from openhands.runtime.utils.edit import FileEditRuntimeMixin


class GeminiFileEditor(FileEditRuntimeMixin):
    """Gemini-style file editor implementation."""

    def __init__(self, *args, **kwargs):
        """Initialize the GeminiFileEditor."""
        super().__init__(*args, **kwargs)
        # No need to initialize file_reader as we'll use file_readers directly

    def read(self, action) -> Observation:
        """Required abstract method implementation."""
        # This is for compatibility with FileEditRuntimeMixin
        # We don't use this method directly
        return ErrorObservation("Use handle_read_file_action instead")

    def write(self, action) -> Observation:
        """Required abstract method implementation."""
        # This is for compatibility with FileEditRuntimeMixin
        # We don't use this method directly
        return ErrorObservation("Use handle_write_file_action instead")

    def run_ipython(self, action) -> Observation:
        """Required abstract method implementation."""
        # This is for compatibility with FileEditRuntimeMixin
        # We don't use this method directly
        return ErrorObservation("IPython not supported in GeminiFileEditor")

    def handle_action(self, action: Action) -> Observation:
        """Handle a file edit action.

        Args:
            action: The action to handle.

        Returns:
            An observation of the result.
        """
        if isinstance(action, GeminiEditAction):
            return self.handle_edit_action(action)
        elif isinstance(action, GeminiWriteFileAction):
            return self.handle_write_file_action(action)
        elif isinstance(action, GeminiReadFileAction):
            return self.handle_read_file_action(action)
        else:
            return ErrorObservation(f'Unsupported action type: {type(action).__name__}')

    def handle_edit_action(self, action: GeminiEditAction) -> Observation:
        """Handle a Gemini-style edit action.

        Args:
            action: The edit action to handle.

        Returns:
            An observation of the result.
        """
        # Validate file path
        if not os.path.isabs(action.file_path):
            return ErrorObservation(f'File path must be absolute: {action.file_path}')

        # Read the file
        read_obs = self.read_file(action.file_path)
        if isinstance(read_obs, ErrorObservation):
            if 'File not found' in read_obs.content:
                # If old_string is empty, create a new file with new_string
                if action.old_string == '':
                    return self.write_file(action.file_path, action.new_string)
                else:
                    return ErrorObservation(
                        'File not found. Cannot apply edit. Use an empty old_string to create a new file.'
                    )
            # Return other error observations as-is
            return read_obs

        # At this point, read_obs must be a FileReadObservation

        # Get the file content
        file_content = read_obs.content

        # Check if old_string is empty (create new file)
        if action.old_string == '':
            return ErrorObservation(
                'Failed to edit. Attempted to create a file that already exists.'
            )

        # Find occurrences of old_string
        occurrences = file_content.count(action.old_string)

        if occurrences == 0:
            return ErrorObservation(
                'Failed to edit, could not find the string to replace.'
            )

        if occurrences != action.expected_replacements:
            return ErrorObservation(
                f'Failed to edit, expected {action.expected_replacements} occurrence(s) but found {occurrences}.'
            )

        # Replace the old_string with new_string
        new_content = file_content.replace(action.old_string, action.new_string)

        # Write the new content
        write_obs = self.write_file(action.file_path, new_content)
        if isinstance(write_obs, ErrorObservation):
            return write_obs

        # Generate diff
        diff = get_diff(file_content, new_content, action.file_path)

        return FileEditObservation(
            content=diff,
            path=action.file_path,
            prev_exist=True,
            old_content=file_content,
            new_content=new_content,
        )

    def handle_write_file_action(self, action: GeminiWriteFileAction) -> Observation:
        """Handle a Gemini-style write file action.

        Args:
            action: The write file action to handle.

        Returns:
            An observation of the result.
        """
        # Validate file path
        if not os.path.isabs(action.file_path):
            return ErrorObservation(f'File path must be absolute: {action.file_path}')

        # Check if file exists
        file_exists = os.path.exists(action.file_path)
        original_content = ''

        if file_exists:
            # Read the existing file
            read_obs = self.read_file(action.file_path)
            if isinstance(read_obs, ErrorObservation):
                return read_obs
            if isinstance(read_obs, FileReadObservation):
                original_content = read_obs.content

        # Write the new content
        write_obs = self.write_file(action.file_path, action.content)
        if isinstance(write_obs, ErrorObservation):
            return write_obs

        # Generate diff
        diff = get_diff(original_content, action.content, action.file_path)

        return FileEditObservation(
            content=diff,
            path=action.file_path,
            prev_exist=file_exists,
            old_content=original_content,
            new_content=action.content,
        )

    def read_file(self, file_path: str) -> Union[FileReadObservation, ErrorObservation]:
        """Read a file.

        Args:
            file_path: The path to the file to read.

        Returns:
            An observation of the file content or an error.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return FileReadObservation(content=content, path=file_path)
        except FileNotFoundError:
            return ErrorObservation(f'File not found: {file_path}')
        except Exception as e:
            return ErrorObservation(f'Error reading file: {str(e)}')

    def write_file(
        self, file_path: str, content: str
    ) -> Union[FileWriteObservation, ErrorObservation]:
        """Write content to a file.

        Args:
            file_path: The path to the file to write to.
            content: The content to write.

        Returns:
            An observation of the write operation or an error.
        """
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return FileWriteObservation(path=file_path, content=content)
        except Exception as e:
            return ErrorObservation(f'Error writing file: {str(e)}')

    def handle_read_file_action(self, action: GeminiReadFileAction) -> Observation:
        """Handle a Gemini-style read file action.

        Args:
            action: The read file action to handle.

        Returns:
            An observation of the result.
        """
        # Validate file path
        if not os.path.isabs(action.absolute_path):
            return ErrorObservation(
                f'File path must be absolute: {action.absolute_path}'
            )

        # Check if file exists
        if not os.path.exists(action.absolute_path):
            return ErrorObservation(f'File not found: {action.absolute_path}')

        # Read the file
        try:
            with open(action.absolute_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ErrorObservation(f'Error reading file: {str(e)}')

        # Handle offset and limit if provided
        if action.offset is not None or action.limit is not None:
            lines = content.splitlines()

            offset = action.offset or 0
            if offset < 0:
                return ErrorObservation(f'Offset must be non-negative: {offset}')

            if offset >= len(lines):
                return ErrorObservation(
                    f'Offset {offset} is out of range for file with {len(lines)} lines'
                )

            if action.limit is not None:
                if action.limit <= 0:
                    return ErrorObservation(f'Limit must be positive: {action.limit}')

                end = min(offset + action.limit, len(lines))
                lines = lines[offset:end]
                content = '\n'.join(lines)

                # Add a note if we truncated the file
                if end < len(lines):
                    content += f'\n\n[Note: Showing lines {offset}-{end - 1} of {len(lines)} total lines]'
            else:
                lines = lines[offset:]
                content = '\n'.join(lines)

                # Add a note if we started from a non-zero offset
                if offset > 0:
                    content += f'\n\n[Note: Showing lines {offset}-{len(lines) - 1} of {len(lines)} total lines]'

        return FileReadObservation(content=content, path=action.absolute_path)

    @classmethod
    def get_supported_tool_names(cls) -> list[str]:
        """Get the names of tools supported by this skill.

        Returns:
            A list of supported tool names.
        """
        return [
            GEMINI_EDIT_TOOL_NAME,
            GEMINI_READ_FILE_TOOL_NAME,
            GEMINI_WRITE_FILE_TOOL_NAME,
        ]

    @classmethod
    def create_action_from_tool_call(
        cls, tool_name: str, tool_args: dict
    ) -> Optional[Action]:
        """Create an action from a tool call.

        Args:
            tool_name: The name of the tool.
            tool_args: The arguments for the tool.

        Returns:
            An action or None if the tool is not supported.
        """
        if tool_name == GEMINI_EDIT_TOOL_NAME:
            return GeminiEditAction(
                file_path=tool_args['file_path'],
                old_string=tool_args['old_string'],
                new_string=tool_args['new_string'],
                expected_replacements=tool_args.get('expected_replacements', 1),
            )
        elif tool_name == GEMINI_WRITE_FILE_TOOL_NAME:
            return GeminiWriteFileAction(
                file_path=tool_args['file_path'],
                content=tool_args['content'],
            )
        elif tool_name == GEMINI_READ_FILE_TOOL_NAME:
            return GeminiReadFileAction(
                absolute_path=tool_args['absolute_path'],
                offset=tool_args.get('offset'),
                limit=tool_args.get('limit'),
            )
        return None
