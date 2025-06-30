from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_EDITOR_TOOL_NAME

_DETAILED_GEMINI_EDITOR_DESCRIPTION = """Gemini-style editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a text file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The following binary file extensions can be viewed in Markdown format: [".xlsx", ".pptx", ".wav", ".mp3", ".m4a", ".flac", ".pdf", ".docx"]. IT DOES NOT HANDLE IMAGES.
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* This tool provides Gemini CLI-style file editing capabilities

Available commands:
- `view`: Display file contents or directory listing
- `create`: Create a new file with specified content
- `replace`: Replace text within a file (similar to Gemini CLI's replace tool)
- `write_file`: Write content to a file (overwrites entire file)
- `read_file`: Read file content with optional line ranges

Before using this tool:
1. Use the view tool to understand the file's contents and context
2. Verify the directory path is correct (only applicable when creating new files):
   - Use the view tool to verify the parent directory exists and is the correct location

When making edits:
   - Ensure the edit results in idiomatic, correct code
   - Do not leave the code in a broken state
   - Always use absolute file paths (starting with /)

CRITICAL REQUIREMENTS FOR USING THE REPLACE COMMAND:

1. EXACT MATCHING: The `old_string` parameter must match EXACTLY one or more consecutive lines from the file, including all whitespace and indentation. The tool will fail if `old_string` matches multiple locations or doesn't match exactly with the file content.

2. UNIQUENESS: The `old_string` must uniquely identify a single instance in the file:
   - Include sufficient context before and after the change point (3-5 lines recommended)
   - If not unique, the replacement will not be performed

3. REPLACEMENT: The `new_string` parameter should contain the edited lines that replace the `old_string`. Both strings must be different.

4. EXPECTED REPLACEMENTS: Use `expected_replacements` parameter when you want to replace multiple occurrences of the same text.

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.
"""

_SHORT_GEMINI_EDITOR_DESCRIPTION = """Gemini-style editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* Provides Gemini CLI-style editing capabilities including replace, write_file, and read_file commands
Notes for using the `replace` command:
* The `old_string` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_string` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_string` to make it unique
* The `new_string` parameter should contain the edited lines that should replace the `old_string`
* Use `expected_replacements` parameter when replacing multiple occurrences
"""


def create_gemini_editor_tool(
    use_short_description: bool = False,
) -> ChatCompletionToolParam:
    description = (
        _SHORT_GEMINI_EDITOR_DESCRIPTION
        if use_short_description
        else _DETAILED_GEMINI_EDITOR_DESCRIPTION
    )
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_EDITOR_TOOL_NAME,
            description=description,
            parameters={
                'type': 'object',
                'properties': {
                    'command': {
                        'description': 'The commands to run. Allowed options are: `view`, `create`, `replace`, `write_file`, `read_file`.',
                        'enum': [
                            'view',
                            'create',
                            'replace',
                            'write_file',
                            'read_file',
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
                    'old_string': {
                        'description': 'Required parameter of `replace` command containing the string in `path` to replace.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'Required parameter of `replace` command containing the new string to replace `old_string` with.',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'description': 'Optional parameter of `replace` command. Number of replacements expected. Defaults to 1 if not specified. Use when you want to replace multiple occurrences.',
                        'type': 'integer',
                        'minimum': 1,
                    },
                    'content': {
                        'description': 'Required parameter of `write_file` command, with the content to write to the file.',
                        'type': 'string',
                    },
                    'offset': {
                        'description': 'Optional parameter of `read_file` command. The 0-based line number to start reading from. Requires `limit` to be set.',
                        'type': 'integer',
                        'minimum': 0,
                    },
                    'limit': {
                        'description': 'Optional parameter of `read_file` command. Maximum number of lines to read. Use with `offset` to paginate through large files.',
                        'type': 'integer',
                        'minimum': 1,
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
