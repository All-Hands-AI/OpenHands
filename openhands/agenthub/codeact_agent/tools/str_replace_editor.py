from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_DETAILED_STR_REPLACE_EDITOR_DESCRIPTION = """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`


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

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.
"""

_SHORT_STR_REPLACE_EDITOR_DESCRIPTION = """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`
Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`
"""


def create_str_replace_editor_tool(
    use_short_description: bool = False,
) -> ChatCompletionToolParam:
    description = (
        _SHORT_STR_REPLACE_EDITOR_DESCRIPTION
        if use_short_description
        else _DETAILED_STR_REPLACE_EDITOR_DESCRIPTION
    )
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='str_replace_editor',
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
