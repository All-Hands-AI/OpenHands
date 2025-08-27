from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.agenthub.codeact_agent.tools.security_utils import (
    RISK_LEVELS,
    SECURITY_RISK_DESC,
)
from openhands.llm.tool_names import STR_REPLACE_EDITOR_TOOL_NAME

_DETAILED_STR_REPLACE_EDITOR_DESCRIPTION = """This tool can create or edit plain text files. It can also view the contents of directories and text files such as plain text, PDF, DOCX, XLSX, and PPTX.  This tool persists the state across multiple commands which allows you to make multiple changes to the same file in separate commands.

- Before editing any file, use the `view` command to understand the file's contents and find a block of text that uniquely identifies the target location of the desired change.
- Always specify absolute file paths starting from the root directory.
- The `view` command returns line numbers similar to the `cat -n` command.
- When you run the `view` command with a directory it lists all non-hidden files and directories up to 2 levels deep starting from the specified directory path.
- When using the str_replace command, the old_str parameter must be both an exact and unique match to the content you intend to replace within the file. An exact match means every character, space, indentation, and line break must be identical to the corresponding section of the file. To ensure the string is unique, which is required for the command to succeed, you must include enough surrounding context—typically 3-5 lines before and after the target lines. The new_str parameter then provides the new content that will completely overwrite the block of text defined by old_str.
- The `create` command will fail if `path` points to an existing file.
-`undo_edit` reverts the last edit made to the specified file."""

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
            name=STR_REPLACE_EDITOR_TOOL_NAME,
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
                        'description': 'Required for the `create` command, with the content of the file to be created.',
                        'type': 'string',
                    },
                    'old_str': {
                        'description': 'Required for the `str_replace` command, contains the string that should be replaced in the file identified by `path`.',
                        'type': 'string',
                    },
                    'new_str': {
                        'description': 'Required for the `insert` command, contains the string to insert. Passes the new text to the `str_replace` command but can be empty if the goal is to delete some text.',
                        'type': 'string',
                    },
                    'insert_line': {
                        'description': 'Required for the `insert` command. The text passed in `new_str` parameter will be inserted AFTER the line `insert_line`.',
                        'type': 'integer',
                    },
                    'view_range': {
                        'description': 'Optional parameter for the `view` command when `path` points to a file, passes the range of line numbers, e.g. [1, 2] will return the first two lines from the file identified by `path`. Setting `[start_line, -1]` shows all lines starting from `start_line`.',
                        'items': {'type': 'integer'},
                        'type': 'array',
                    },
                    # 'security_risk': {
                    #     'type': 'string',
                    #     'description': SECURITY_RISK_DESC,
                    #     'enum': RISK_LEVELS,
                    # },
                },
                'required': ['command', 'path', 'security_risk'],
            },
        ),
    )
