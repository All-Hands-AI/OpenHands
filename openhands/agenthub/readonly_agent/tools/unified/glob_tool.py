"""
GlobTool for ReadOnlyAgent - safe file pattern matching.
"""

from typing import Any, Dict
from openhands.agenthub.codeact_agent.tools.unified.base import Tool, ToolValidationError


class GlobTool(Tool):
    """Tool for safely finding files using glob patterns without modification."""
    
    def __init__(self):
        super().__init__('glob', 'Find files using glob patterns safely')
    
    def get_schema(self):
        return {
            'type': 'function',
            'function': {
                'name': 'glob',
                'description': """Find files and directories using glob patterns.
* Use wildcards to find files matching patterns
* Supports standard glob patterns: *, ?, [abc], **
* Returns list of matching file paths
* Use this to find files by extension, name patterns, or directory structure""",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'pattern': {
                            'type': 'string',
                            'description': 'The glob pattern to match files (e.g., "*.py", "**/*.js", "test_*.py")',
                        },
                        'base_path': {
                            'type': 'string',
                            'description': 'The base directory to search from (defaults to current directory)',
                            'default': '.',
                        },
                    },
                    'required': ['pattern'],
                },
            },
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate glob tool parameters."""
        if not isinstance(parameters, dict):
            raise ToolValidationError("Parameters must be a dictionary")
        
        # Validate required pattern parameter
        if 'pattern' not in parameters:
            raise ToolValidationError("Missing required parameter: pattern")
        
        pattern = parameters['pattern']
        if not isinstance(pattern, str):
            raise ToolValidationError("Parameter 'pattern' must be a string")
        
        if not pattern.strip():
            raise ToolValidationError("Parameter 'pattern' cannot be empty")
        
        validated = {'pattern': pattern.strip()}
        
        # Validate optional base_path parameter
        if 'base_path' in parameters:
            base_path = parameters['base_path']
            if not isinstance(base_path, str):
                raise ToolValidationError("Parameter 'base_path' must be a string")
            validated['base_path'] = base_path.strip() if base_path.strip() else '.'
        else:
            validated['base_path'] = '.'  # Default value
        
        return validated