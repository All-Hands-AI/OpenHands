"""SearchRepoTool for searching code snippets based on terms or line numbers."""

from typing import Any

from litellm import ChatCompletionToolParam

from openhands.agenthub.codeact_agent.tools.unified.base import (
    Tool,
    ToolValidationError,
)


class SearchRepoTool(Tool):
    """Tool for searching the codebase to retrieve relevant code snippets.

    Can search based on terms/keywords or specific line numbers within files.
    """

    def __init__(self):
        super().__init__(
            name='search_code_snippets',
            description='Searches the codebase to retrieve relevant code snippets based on given queries',
        )

    def get_schema(
        self, use_short_description: bool = False
    ) -> ChatCompletionToolParam:
        """Get the tool schema for function calling."""
        description = """Searches the codebase to retrieve relevant code snippets based on given queries(terms or line numbers).
** Note:
- Either `search_terms` or `line_nums` must be provided to perform a search.
- If `search_terms` are provided, it searches for code snippets based on each term:
- If `line_nums` is provided, it searches for code snippets around the specified lines within the file defined by `file_path_or_pattern`.

** Example Usage:
# Search for code content contain keyword `order`, `bill`
search_code_snippets(search_terms=["order", "bill"])

# Search for a class
search_code_snippets(search_terms=["MyClass"])

# Search for context around specific lines (10 and 15) within a file
search_code_snippets(line_nums=[10, 15], file_path_or_pattern='src/example.py')
"""

        if use_short_description:
            description = 'Searches the codebase to retrieve relevant code snippets based on given queries'

        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': description.strip(),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'search_terms': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'A list of names, keywords, or code snippets to search for within the codebase. '
                            'This can include potential function names, class names, or general code fragments. '
                            'Either `search_terms` or `line_nums` must be provided to perform a search.',
                        },
                        'line_nums': {
                            'type': 'array',
                            'items': {'type': 'integer'},
                            'description': 'Specific line numbers to locate code snippets within a specified file. '
                            'Must be used alongside a valid `file_path_or_pattern`. '
                            'Either `line_nums` or `search_terms` must be provided to perform a search.',
                        },
                        'file_path_or_pattern': {
                            'type': 'string',
                            'description': 'A glob pattern or specific file path used to filter search results '
                            'to particular files or directories. Defaults to "**/*.py", meaning all Python files are searched by default. '
                            'If `line_nums` are provided, this must specify a specific file path.',
                            'default': '**/*.py',
                        },
                    },
                    'required': [],
                },
            },
        }

    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tool parameters."""
        search_terms = parameters.get('search_terms')
        line_nums = parameters.get('line_nums')
        file_path_or_pattern = parameters.get('file_path_or_pattern', '**/*.py')

        # Either search_terms or line_nums must be provided
        if not search_terms and not line_nums:
            raise ToolValidationError(
                "Either 'search_terms' or 'line_nums' must be provided"
            )

        # Validate search_terms if provided
        if search_terms is not None:
            if not isinstance(search_terms, list):
                raise ToolValidationError("Parameter 'search_terms' must be a list")

            for i, term in enumerate(search_terms):
                if not isinstance(term, str):
                    raise ToolValidationError(
                        f'Search term at index {i} must be a string'
                    )
                if not term.strip():
                    raise ToolValidationError(
                        f'Search term at index {i} cannot be empty'
                    )

        # Validate line_nums if provided
        if line_nums is not None:
            if not isinstance(line_nums, list):
                raise ToolValidationError("Parameter 'line_nums' must be a list")

            for i, line_num in enumerate(line_nums):
                if not isinstance(line_num, int):
                    raise ToolValidationError(
                        f'Line number at index {i} must be an integer'
                    )
                if line_num < 1:
                    raise ToolValidationError(
                        f'Line number at index {i} must be positive'
                    )

        # Validate file_path_or_pattern
        if not isinstance(file_path_or_pattern, str):
            raise ToolValidationError(
                "Parameter 'file_path_or_pattern' must be a string"
            )

        # If line_nums is provided, file_path_or_pattern should be a specific file
        if line_nums and file_path_or_pattern == '**/*.py':
            raise ToolValidationError(
                "When 'line_nums' is provided, 'file_path_or_pattern' must specify a specific file path"
            )

        # Normalize parameters
        result: dict[str, Any] = {'file_path_or_pattern': file_path_or_pattern.strip()}

        if search_terms:
            result['search_terms'] = [term.strip() for term in search_terms]

        if line_nums:
            result['line_nums'] = line_nums

        return result
