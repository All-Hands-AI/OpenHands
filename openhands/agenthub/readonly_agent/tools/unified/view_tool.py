"""
ViewTool for ReadOnlyAgent - safe file/directory viewing.
"""

from typing import Any, Dict
from openhands.agenthub.codeact_agent.tools.unified.base import Tool, ToolValidationError


class ViewTool(Tool):
    """Tool for safely viewing files and directories without modification."""
    
    def __init__(self):
        super().__init__('view', 'View files and directories safely')
    
    def get_schema(self, use_short_description: bool = False):
        return {
            'type': 'function',
            'function': {
                'name': 'view',
                'description': """Reads a file or list directories from the local filesystem.
* The path parameter must be an absolute path, not a relative path.
* If `path` is a file, `view` displays the result of applying `cat -n`; if `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep.
* You can optionally specify a line range to view (especially handy for long files), but it's recommended to read the whole file by not providing this parameter.
* For image files, the tool will display the image for you.
* For large files that exceed the display limit:
  - The output will be truncated and marked with `<response clipped>`
  - Use the `view_range` parameter to view specific sections after the truncation point""",
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'The absolute path to the file to read or directory to list',
                        },
                        'view_range': {
                            'description': 'Optional parameter of `view` command when `path` points to a *file*. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.',
                            'items': {'type': 'integer'},
                            'type': 'array',
                        },
                    },
                    'required': ['path'],
                },
            },
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate view tool parameters."""
        if not isinstance(parameters, dict):
            raise ToolValidationError("Parameters must be a dictionary")
        
        # Validate required path parameter
        if 'path' not in parameters:
            raise ToolValidationError("Missing required parameter: path")
        
        path = parameters['path']
        if not isinstance(path, str):
            raise ToolValidationError("Parameter 'path' must be a string")
        
        if not path.strip():
            raise ToolValidationError("Parameter 'path' cannot be empty")
        
        validated: dict[str, Any] = {'path': path.strip()}
        
        # Validate optional view_range parameter
        if 'view_range' in parameters:
            view_range = parameters['view_range']
            if view_range is not None:
                if not isinstance(view_range, list):
                    raise ToolValidationError("Parameter 'view_range' must be a list")
                
                if len(view_range) != 2:
                    raise ToolValidationError("Parameter 'view_range' must contain exactly 2 elements")
                
                if not all(isinstance(x, int) for x in view_range):
                    raise ToolValidationError("Parameter 'view_range' elements must be integers")
                
                start, end = view_range
                if start < 1:
                    raise ToolValidationError("Parameter 'view_range' start must be >= 1")
                
                if end != -1 and end < start:
                    raise ToolValidationError("Parameter 'view_range' end must be >= start or -1")
                
                validated['view_range'] = view_range
        
        return validated