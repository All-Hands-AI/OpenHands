from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_EDIT_TOOL_NAME, GEMINI_WRITE_FILE_TOOL_NAME

_GEMINI_EDIT_TOOL_DESCRIPTION = """Replaces text within a file. By default, replaces a single occurrence, but can replace multiple occurrences when `expected_replacements` is specified. This tool requires providing significant context around the change to ensure precise targeting.

Expectation for required parameters:
1. `file_path` MUST be an absolute path; otherwise an error will be thrown.
2. `old_string` MUST be the exact literal text to replace (including all whitespace, indentation, newlines, and surrounding code etc.).
3. `new_string` MUST be the exact literal text to replace `old_string` with (also including all whitespace, indentation, newlines, and surrounding code etc.). Ensure the resulting code is correct and idiomatic.
4. NEVER escape `old_string` or `new_string`, that would break the exact literal text requirement.

**Important:** If ANY of the above are not satisfied, the tool will fail. CRITICAL for `old_string`: Must uniquely identify the single instance to change. Include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. If this string matches multiple locations, or does not match exactly, the tool will fail.

**Multiple replacements:** Set `expected_replacements` to the number of occurrences you want to replace. The tool will replace ALL occurrences that match `old_string` exactly. Ensure the number of replacements matches your expectation.
"""

_GEMINI_WRITE_FILE_TOOL_DESCRIPTION = """Writes content to a specified file in the local filesystem.

The file_path must be an absolute path (e.g., '/home/user/project/file.txt'). Relative paths are not supported.
If the file doesn't exist, it will be created. If it exists, it will be overwritten.
"""

def create_gemini_edit_tool() -> ChatCompletionToolParam:
    """Creates a Gemini-style edit tool for replacing text in files."""
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_EDIT_TOOL_NAME,
            description=_GEMINI_EDIT_TOOL_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': "The absolute path to the file to modify. Must start with '/'.",
                        'type': 'string',
                    },
                    'old_string': {
                        'description': 'The exact literal text to replace, preferably unescaped. For single replacements (default), include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. For multiple replacements, specify expected_replacements parameter. If this string is not the exact literal text (i.e. you escaped it) or does not match exactly, the tool will fail.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'The exact literal text to replace `old_string` with, preferably unescaped. Provide the EXACT text. Ensure the resulting code is correct and idiomatic.',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'type': 'number',
                        'description': 'Number of replacements expected. Defaults to 1 if not specified. Use when you want to replace multiple occurrences.',
                        'minimum': 1,
                    },
                },
                'required': ['file_path', 'old_string', 'new_string'],
            },
        ),
    )

def create_gemini_write_file_tool() -> ChatCompletionToolParam:
    """Creates a Gemini-style write file tool for writing content to files."""
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_WRITE_FILE_TOOL_NAME,
            description=_GEMINI_WRITE_FILE_TOOL_DESCRIPTION,
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported.",
                        'type': 'string',
                    },
                    'content': {
                        'description': 'The content to write to the file.',
                        'type': 'string',
                    },
                },
                'required': ['file_path', 'content'],
            },
        ),
    )