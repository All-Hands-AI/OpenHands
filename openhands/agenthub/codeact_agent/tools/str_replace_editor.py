from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_DETAILED_STR_REPLACE_EDITOR_DESCRIPTION = """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. Remember, `cat -n` outputs line numbers too, which are **not** actually in the file. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

### **CRITICAL NOTES FOR USING `str_replace`**
1. **IGNORE LINE NUMBERS**:
   - The `view` command includes line numbers for reference, but these numbers **are not part of the actual file**.
   - **Do not include line numbers in `old_str` or `new_str` when using `str_replace`**, as this will cause the edit to fail.

2. **EXACT MATCHING REQUIRED**:
   - The `old_str` parameter must match **exactly** one or more consecutive lines from the actual file (excluding line numbers), including all whitespace and indentation.
   - If `old_str` is not unique in the file, the replacement will not be performed.

3. **REPLACEMENT RULES**:
   - The `new_str` parameter should contain only the edited lines that replace the `old_str`.
   - Both `old_str` and `new_str` must be different.

### **Workflow to Ensure Correct Edits**
1. **Use `view` to inspect the file**, but remember that line numbers are only for reference.
2. **When extracting `old_str`, remove the line numbers**, and ensure it matches the actual file content.
3. **Submit edits in a single message** when making multiple replacements in the same file.

Failing to remove line numbers from `old_str` will cause the edit to be rejected.
"""


_SIMPLIFIED_STR_REPLACE_EDITOR_DESCRIPTION = """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. **These line numbers are not part of the actual file** and should be ignored when using `str_replace`.
* If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

### **Important for `str_replace`**
- **IGNORE LINE NUMBERS**: The `view` output includes line numbers, but they should **not** be included in `old_str` or `new_str` as they are not in the actual file.
- **MATCH EXACTLY**: `old_str` must match **one or more consecutive lines exactly** (excluding line numbers) for the replacement to work.
- **ENSURE UNIQUENESS**: If `old_str` appears multiple times in the file, the replacement will fail.

Failing to remove line numbers from `old_str` will cause the edit to be rejected.
"""


def create_str_replace_editor_tool(
    use_simplified_description: bool = False,
) -> ChatCompletionToolParam:
    description = (
        _SIMPLIFIED_STR_REPLACE_EDITOR_DESCRIPTION
        if use_simplified_description
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
