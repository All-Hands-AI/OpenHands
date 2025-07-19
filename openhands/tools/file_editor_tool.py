"""File editor tool for OpenHands using str_replace_editor interface."""

from typing import Any, Dict, List, Optional

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk


from openhands.llm.tool_names import STR_REPLACE_EDITOR_TOOL_NAME

from .base import Tool, ToolValidationError


class FileEditorTool(Tool):
    """Tool for viewing, creating and editing files using str_replace_editor interface."""
    
    def __init__(self):
        super().__init__(
            name=STR_REPLACE_EDITOR_TOOL_NAME,
            description="Custom editing tool for viewing, creating and editing files"
        )
    
    def get_schema(self, use_short_description: bool = False) -> ChatCompletionToolParam:
        """Get the tool schema for function calling."""
        if use_short_description:
            description = self._get_short_description()
        else:
            description = self._get_detailed_description()
            
        return ChatCompletionToolParam(
            type='function',
            function=ChatCompletionToolParamFunctionChunk(
                name=self.name,
                description=description,
                parameters={
                    'type': 'object',
                    'properties': {
                        'command': {
                            'description': 'The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.',
                            'enum': [
                                'view',
                                'create',
                                'str_replace',
                                'insert',
                                'undo_edit',
                            ],
                            'type': 'string',
                        },
                        'path': {
                            'description': 'Absolute path to file or directory, e.g. `/workspace/file.py` or `/workspace`.',
                            'type': 'string',
                        },
                        'file_text': {
                            'description': 'Required parameter of `create` command, with the content of the file to be created.',
                            'type': 'string',
                        },
                        'old_str': {
                            'description': 'Required parameter of `str_replace` command containing the string in `path` to replace.',
                            'type': 'string',
                        },
                        'new_str': {
                            'description': 'Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.',
                            'type': 'string',
                        },
                        'insert_line': {
                            'description': 'Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.',
                            'type': 'integer',
                        },
                        'view_range': {
                            'description': 'Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.',
                            'items': {'type': 'integer'},
                            'type': 'array',
                        },
                    },
                    'required': ['command', 'path'],
                },
            ),
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize file editor tool parameters."""
        if 'command' not in parameters:
            raise ToolValidationError("Missing required parameter 'command'")
        if 'path' not in parameters:
            raise ToolValidationError("Missing required parameter 'path'")
        
        command = parameters['command']
        valid_commands = ['view', 'create', 'str_replace', 'insert', 'undo_edit']
        if command not in valid_commands:
            raise ToolValidationError(f"Invalid command '{command}'. Must be one of: {valid_commands}")
        
        validated = {
            'command': command,
            'path': str(parameters['path']),
        }
        
        # Validate command-specific parameters
        if command == 'create':
            if 'file_text' not in parameters:
                raise ToolValidationError("'create' command requires 'file_text' parameter")
            validated['file_text'] = str(parameters['file_text'])
        
        elif command == 'str_replace':
            if 'old_str' not in parameters:
                raise ToolValidationError("'str_replace' command requires 'old_str' parameter")
            validated['old_str'] = str(parameters['old_str'])
            validated['new_str'] = str(parameters.get('new_str', ''))
        
        elif command == 'insert':
            if 'insert_line' not in parameters:
                raise ToolValidationError("'insert' command requires 'insert_line' parameter")
            if 'new_str' not in parameters:
                raise ToolValidationError("'insert' command requires 'new_str' parameter")
            
            try:
                validated['insert_line'] = int(parameters['insert_line'])
            except (ValueError, TypeError):
                raise ToolValidationError(f"Invalid insert_line value: {parameters['insert_line']}")
            
            validated['new_str'] = str(parameters['new_str'])
        
        elif command == 'view':
            if 'view_range' in parameters:
                view_range = parameters['view_range']
                if not isinstance(view_range, list) or len(view_range) != 2:
                    raise ToolValidationError("view_range must be a list of two integers")
                try:
                    validated['view_range'] = [int(view_range[0]), int(view_range[1])]
                except (ValueError, TypeError):
                    raise ToolValidationError("view_range must contain valid integers")
        
        return validated
    

    
    def _get_detailed_description(self) -> str:
        """Get detailed description for the tool."""
        return """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a text file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The following binary file extensions can be viewed in Markdown format: [".xlsx", ".pptx", ".wav", ".mp3", ".m4a", ".flac", ".pdf", ".docx"]. IT DOES NOT HANDLE IMAGES.
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`
* This tool can be used for creating and editing files in plain-text format.


Before using this tool:
1. Use the view tool to understand the file's contents and context
2. Verify the directory path is correct (only applicable when creating new files):
   - Use the view tool to verify the parent directory exists and is the correct location

When making edits:
   - Ensure the edit results in idiomatic, correct code
   - Do not leave the code in a broken state
   - Always use absolute file paths (starting with /)

CRITICAL REQUIREMENTS FOR USING THIS TOOL:

1. EXACT MATCHING: The `old_str` parameter must match EXACTLY one or more consecutive lines from the file, including all whitespace and indentation. The tool will fail if `old_str` matches multiple locations or doesn't match exactly with the file content.

2. UNIQUENESS: The `old_str` must uniquely identify a single instance in the file:
   - Include sufficient context before and after the change point (3-5 lines recommended)
   - If not unique, the replacement will not be performed

3. REPLACEMENT: The `new_str` parameter should contain the edited lines that replace the `old_str`. Both strings must be different.

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each."""
    
    def _get_short_description(self) -> str:
        """Get short description for the tool."""
        return """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`
Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`"""