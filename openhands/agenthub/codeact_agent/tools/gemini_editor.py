"""
Gemini-style editing tool for OpenHands.

This implementation is based on the Gemini CLI tools from Google LLC.
Original source: https://github.com/google-gemini/gemini-cli

Copyright 2025 Google LLC
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Modifications made for OpenHands integration:
- Adapted tool signatures to match OpenHands ChatCompletionToolParam format
- Combined multiple tools into a single unified interface
- Added OpenHands-specific configuration and integration
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_EDITOR_TOOL_NAME

_DETAILED_GEMINI_EDITOR_DESCRIPTION = """Unified file editing tool with Gemini CLI-compatible commands

This tool provides access to the following file operations:
- `read_file`: Read content from files
- `write_file`: Write content to files
- `replace`: Replace text within files
- `list_directory`: List directory contents

Each command matches the exact signature of the corresponding Gemini CLI tool.
Use absolute file paths (starting with /) for all operations.

For the `replace` command:
- The `old_string` must match EXACTLY, including whitespace and indentation
- Include sufficient context (3-5 lines) to ensure uniqueness
- The `new_string` should contain the complete replacement text
- Use `expected_replacements` parameter for multiple replacements
"""

_SHORT_GEMINI_EDITOR_DESCRIPTION = """Unified file tool with Gemini CLI commands

Provides read_file, write_file, replace, and list_directory commands with exact Gemini CLI signatures.
Use absolute paths for all operations.

For replace operations:
- Match text exactly (including whitespace)
- Include context to ensure uniqueness
- Provide complete replacement text
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
                        'description': 'The commands to run. Allowed options are: `read_file`, `write_file`, `replace`, `list_directory`.',
                        'enum': [
                            'read_file',
                            'write_file',
                            'replace',
                            'list_directory',
                        ],
                        'type': 'string',
                    },
                    # read_file parameters (matching ReadFileTool from Gemini CLI)
                    'absolute_path': {
                        'description': "The absolute path to the file to read (e.g., '/home/user/project/file.txt'). Relative paths are not supported. You must provide an absolute path.",
                        'type': 'string',
                        'pattern': '^/',
                    },
                    'offset': {
                        'description': "Optional: For text files, the 0-based line number to start reading from. Requires 'limit' to be set. Use for paginating through large files.",
                        'type': 'number',
                    },
                    'limit': {
                        'description': "Optional: For text files, maximum number of lines to read. Use with 'offset' to paginate through large files. If omitted, reads the entire file (if feasible, up to a default limit).",
                        'type': 'number',
                    },
                    # write_file parameters (matching WriteFileTool from Gemini CLI)
                    'file_path': {
                        'description': "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported.",
                        'type': 'string',
                    },
                    'content': {
                        'description': 'The content to write to the file.',
                        'type': 'string',
                    },
                    # replace parameters (matching EditTool from Gemini CLI)
                    'old_string': {
                        'description': 'The exact literal text to replace, preferably unescaped. For single replacements (default), include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. For multiple replacements, specify expected_replacements parameter. If this string is not the exact literal text (i.e. you escaped it) or does not match exactly, the tool will fail.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'The exact literal text to replace `old_string` with, preferably unescaped. Provide the EXACT text. Ensure the resulting code is correct and idiomatic.',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'description': 'Number of replacements expected. Defaults to 1 if not specified. Use when you want to replace multiple occurrences.',
                        'type': 'number',
                        'minimum': 1,
                    },
                    # list_directory parameters (matching LSTool from Gemini CLI)
                    'path': {
                        'description': 'The absolute path to the directory to list (must be absolute, not relative)',
                        'type': 'string',
                    },
                    'ignore': {
                        'description': 'List of glob patterns to ignore',
                        'items': {
                            'type': 'string',
                        },
                        'type': 'array',
                    },
                    'respect_git_ignore': {
                        'description': 'Optional: Whether to respect .gitignore patterns when listing files. Only available in git repositories. Defaults to true.',
                        'type': 'boolean',
                    },
                },
                'required': ['command'],
            },
        ),
    )
