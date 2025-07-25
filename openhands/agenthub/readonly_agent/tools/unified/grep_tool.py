"""
GrepTool for ReadOnlyAgent - safe text searching.
"""

from typing import Any, Dict
from openhands.agenthub.codeact_agent.tools.unified.base import Tool, ToolValidationError


class GrepTool(Tool):
    """Tool for safely searching text in files without modification."""
    
    def __init__(self):
        super().__init__('grep', 'Search for patterns in files safely')
    
    def get_schema(self):
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
                            'description': 'The directory or file path to search in',
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
                    'required': ['pattern', 'path'],
                },
            },
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate grep tool parameters."""
        if not isinstance(parameters, dict):
            raise ToolValidationError("Parameters must be a dictionary")
        
        # Validate required parameters
        if 'pattern' not in parameters:
            raise ToolValidationError("Missing required parameter: pattern")
        if 'path' not in parameters:
            raise ToolValidationError("Missing required parameter: path")
        
        pattern = parameters['pattern']
        path = parameters['path']
        
        if not isinstance(pattern, str):
            raise ToolValidationError("Parameter 'pattern' must be a string")
        if not isinstance(path, str):
            raise ToolValidationError("Parameter 'path' must be a string")
        
        if not pattern.strip():
            raise ToolValidationError("Parameter 'pattern' cannot be empty")
        if not path.strip():
            raise ToolValidationError("Parameter 'path' cannot be empty")
        
        validated = {
            'pattern': pattern.strip(),
            'path': path.strip()
        }
        
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
                raise ToolValidationError("Parameter 'case_sensitive' must be a boolean")
            validated['case_sensitive'] = case_sensitive
        else:
            validated['case_sensitive'] = False  # Default value
        
        return validated