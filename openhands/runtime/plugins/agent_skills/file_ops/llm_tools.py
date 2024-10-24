"""llm_tools.py

This module provides LLM tool functions based on the file operations from file_ops.py.
It includes function schemas and implementations that can be registered with LLM function calling capabilities.
"""

from typing import Any, List, Optional

from openhands.runtime.plugins.agent_skills.file_ops import file_ops

# Function schemas that describe each tool function for the LLM
TOOL_SCHEMAS = [
    {
        'name': 'open_file',
        'description': 'Opens and reads a file, optionally starting from a specific line with context.',
        'parameters': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the file to open',
                },
                'line_number': {
                    'type': 'integer',
                    'description': 'The line number to start reading from',
                    'default': 1,
                },
                'context_lines': {
                    'type': 'integer',
                    'description': 'Number of context lines to show',
                    'default': 100,
                },
            },
            'required': ['path'],
        },
    },
    {
        'name': 'search_file',
        'description': 'Searches for a term in a specific file or the currently open file.',
        'parameters': {
            'type': 'object',
            'properties': {
                'search_term': {
                    'type': 'string',
                    'description': 'The term to search for',
                },
                'file_path': {
                    'type': 'string',
                    'description': 'Optional path to the file to search',
                },
            },
            'required': ['search_term'],
        },
    },
    {
        'name': 'search_dir',
        'description': 'Searches for a term in all files in a directory.',
        'parameters': {
            'type': 'object',
            'properties': {
                'search_term': {
                    'type': 'string',
                    'description': 'The term to search for',
                },
                'dir_path': {
                    'type': 'string',
                    'description': 'The directory path to search in',
                    'default': './',
                },
            },
            'required': ['search_term'],
        },
    },
    {
        'name': 'find_file',
        'description': 'Finds all files with a given name in a directory.',
        'parameters': {
            'type': 'object',
            'properties': {
                'file_name': {
                    'type': 'string',
                    'description': 'The name of the file to find',
                },
                'dir_path': {
                    'type': 'string',
                    'description': 'The directory path to search in',
                    'default': './',
                },
            },
            'required': ['file_name'],
        },
    },
]


class FileTools:
    """A class that provides file operation tools for LLMs."""

    def __init__(self):
        self._capture_buffer = []

    def _get_and_clear_buffer(self) -> str:
        """Gets the captured output and clears the buffer."""
        result = '\n'.join(self._capture_buffer)
        self._capture_buffer.clear()
        return result

    def _capture_output(self, func, *args, **kwargs):
        """Capture the output of a function."""
        import io
        import sys

        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        try:
            func(*args, **kwargs)
            output = new_stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return output

    def open_file(
        self, path: str, line_number: int = 1, context_lines: int = 100
    ) -> str:
        """Tool function for opening and reading files."""
        try:
            output = self._capture_output(
                file_ops.open_file, path, line_number, context_lines
            )
            self._capture_buffer.append(output)
            return self._get_and_clear_buffer()
        except Exception as e:
            return f'Error: {str(e)}'

    def search_file(self, search_term: str, file_path: Optional[str] = None) -> str:
        """Tool function for searching in files."""
        try:
            output = self._capture_output(file_ops.search_file, search_term, file_path)
            self._capture_buffer.append(output)
            return self._get_and_clear_buffer()
        except Exception as e:
            return f'Error: {str(e)}'

    def search_dir(self, search_term: str, dir_path: str = './') -> str:
        """Tool function for searching in directories."""
        try:
            output = self._capture_output(file_ops.search_dir, search_term, dir_path)
            self._capture_buffer.append(output)
            return self._get_and_clear_buffer()
        except Exception as e:
            return f'Error: {str(e)}'

    def find_file(self, file_name: str, dir_path: str = './') -> str:
        """Tool function for finding files."""
        try:
            output = self._capture_output(file_ops.find_file, file_name, dir_path)
            self._capture_buffer.append(output)
            return self._get_and_clear_buffer()
        except Exception as e:
            return f'Error: {str(e)}'


def get_tool_schemas() -> List[dict[str, Any]]:
    """Returns the list of tool function schemas."""
    return TOOL_SCHEMAS


def get_tool_functions() -> dict[str, Any]:
    """Returns a dictionary mapping function names to their implementations."""
    tools = FileTools()
    return {
        'open_file': tools.open_file,
        'search_file': tools.search_file,
        'search_dir': tools.search_dir,
        'find_file': tools.find_file,
    }
