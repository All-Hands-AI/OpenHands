"""SearchEntityTool for retrieving complete implementations of specified entities."""

from typing import Any

from litellm import ChatCompletionToolParam

from openhands.agenthub.codeact_agent.tools.base import Tool
from openhands.core.exceptions import FunctionCallValidationError as ToolValidationError


class SearchEntityTool(Tool):
    """Tool for searching and retrieving complete implementations of specified entities.

    This tool can handle specific entity queries such as function names, class names, or file paths.
    """

    def __init__(self):
        super().__init__(
            name='get_entity_contents',
            description='Searches the codebase to retrieve the complete implementations of specified entities',
        )

    def get_schema(
        self, use_short_description: bool = False
    ) -> ChatCompletionToolParam:
        """Get the tool schema for function calling."""
        description = """
Searches the codebase to retrieve the complete implementations of specified entities based on the provided entity names.
The tool can handle specific entity queries such as function names, class names, or file paths.

**Usage Example:**
# Search for a specific function implementation
get_entity_contents(['src/my_file.py:MyClass.func_name'])

# Search for a file's complete content
get_entity_contents(['src/my_file.py'])

**Entity Name Format:**
- To specify a function or class, use the format: `file_path:QualifiedName`
  (e.g., 'src/helpers/math_helpers.py:MathUtils.calculate_sum').
- To search for a file's content, use only the file path (e.g., 'src/my_file.py').
"""

        if use_short_description:
            description = 'Searches the codebase to retrieve the complete implementations of specified entities'

        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': description.strip(),
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'entity_names': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': (
                                'A list of entity names to query. Each entity name can represent a function, class, or file. '
                                "For functions or classes, the format should be 'file_path:QualifiedName' "
                                "(e.g., 'src/helpers/math_helpers.py:MathUtils.calculate_sum'). "
                                "For files, use just the file path (e.g., 'src/my_file.py')."
                            ),
                        }
                    },
                    'required': ['entity_names'],
                },
            },
        }

    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tool parameters."""
        if 'entity_names' not in parameters:
            raise ToolValidationError("Missing required parameter 'entity_names'")

        entity_names = parameters['entity_names']

        # Validate entity_names is a list
        if not isinstance(entity_names, list):
            raise ToolValidationError("Parameter 'entity_names' must be a list")

        # Validate each entity name is a string
        for i, entity_name in enumerate(entity_names):
            if not isinstance(entity_name, str):
                raise ToolValidationError(f'Entity name at index {i} must be a string')
            if not entity_name.strip():
                raise ToolValidationError(f'Entity name at index {i} cannot be empty')

        # Normalize: strip whitespace from entity names
        normalized_entity_names = [name.strip() for name in entity_names]

        return {'entity_names': normalized_entity_names}
