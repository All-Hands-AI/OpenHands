from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_STR_REPLACE_EDITOR_DESCRIPTION = """Text editor for viewing, creating and editing files
* State persists across commands and user discussions
* `view`: For files shows numbered content (`cat -n`); for directories lists files up to 2 levels
* `create`: Cannot overwrite existing files
* Long outputs are truncated with `<response clipped>`
* `undo_edit`: Reverts last edit to file

Before using:
1. Use `view` to understand file contents
2. For new files, verify parent directory exists

When editing:
- Ensure edits produce correct, idiomatic code
- Use absolute file paths (starting with /)

CRITICAL REQUIREMENTS:
1. EXACT MATCHING: `old_str` must match EXACTLY consecutive lines including whitespace
2. UNIQUENESS: Include enough context to ensure unique identification (recommend 3-5 lines before and after)
3. REPLACEMENT: `new_str` replaces `old_str` and must differ from it

For multiple edits to same file, prefer single message with multiple tool calls
"""

StrReplaceEditorTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='str_replace_editor',
        description=_STR_REPLACE_EDITOR_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'command': {
                    'description': 'The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.',
                    'enum': ['view', 'create', 'str_replace', 'insert', 'undo_edit'],
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
