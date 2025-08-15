"""
GrepTool for ReadOnlyAgent - safe text searching.
"""

from typing import Any

from openhands.agenthub.codeact_agent.tools.base import Tool
from openhands.core.exceptions import FunctionCallValidationError as ToolValidationError


class GrepTool(Tool):
    """Tool for safely searching text in files without modification."""

    def __init__(self):
        super().__init__('grep', 'Search for patterns in files safely')

    def get_schema(self, use_short_description: bool = False):
        return {
            'type': 'function',
            'function': {
                'name': 'grep',
                'description': """Search for patterns in files using grep.
* Searches for a pattern in files within a directory
* Returns matching lines with line numbers and file paths
* Supports basic regex patterns
* Use this to find specific code patterns, function definitions, or text content""",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'pattern': {
                            'type': 'string',
                            'description': 'The pattern to search for (supports basic regex)',
                        },
                        'path': {
                            'type': 'string',
                            'description': 'The directory or file path to search in (optional, defaults to current directory)',
                        },
                        'include': {
                            'type': 'string',
                            'description': 'Optional file pattern to filter which files to search (e.g., "*.js", "*.{ts,tsx}")',
                        },
                        'recursive': {
                            'type': 'boolean',
                            'description': 'Whether to search recursively in subdirectories',
                            'default': True,
                        },
                        'case_sensitive': {
                            'type': 'boolean',
                            'description': 'Whether the search should be case sensitive',
                            'default': False,
                        },
                    },
                    'required': ['pattern'],
                },
            },
        }

    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate grep tool parameters."""
        if not isinstance(parameters, dict):
            raise ToolValidationError('Parameters must be a dictionary')

        # Validate required parameters
        if 'pattern' not in parameters:
            raise ToolValidationError('Missing required parameter: pattern')

        pattern = parameters['pattern']

        if not isinstance(pattern, str):
            raise ToolValidationError("Parameter 'pattern' must be a string")

        if not pattern.strip():
            raise ToolValidationError("Parameter 'pattern' cannot be empty")

        validated: dict[str, Any] = {'pattern': pattern.strip()}

        # Validate optional path parameter
        if 'path' in parameters:
            path = parameters['path']
            if not isinstance(path, str):
                raise ToolValidationError("Parameter 'path' must be a string")
            if not path.strip():
                raise ToolValidationError("Parameter 'path' cannot be empty")
            validated['path'] = path.strip()

        # Handle include parameter (legacy compatibility)
        if 'include' in parameters:
            include = parameters['include']
            if not isinstance(include, str):
                raise ToolValidationError("Parameter 'include' must be a string")
            validated['include'] = include.strip()

        # Validate optional parameters
        if 'recursive' in parameters:
            recursive = parameters['recursive']
            if not isinstance(recursive, bool):
                raise ToolValidationError("Parameter 'recursive' must be a boolean")
            validated['recursive'] = recursive
        else:
            validated['recursive'] = True  # Default value

        if 'case_sensitive' in parameters:
            case_sensitive = parameters['case_sensitive']
            if not isinstance(case_sensitive, bool):
                raise ToolValidationError(
                    "Parameter 'case_sensitive' must be a boolean"
                )
            validated['case_sensitive'] = case_sensitive
        else:
            validated['case_sensitive'] = False  # Default value

        return validated
