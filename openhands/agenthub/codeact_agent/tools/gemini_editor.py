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

_DETAILED_GEMINI_EDITOR_DESCRIPTION = """Gemini-style editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* This tool provides Gemini CLI-style file editing capabilities based on the official Google Gemini CLI tools
* The following binary file extensions can be viewed in Markdown format: [".xlsx", ".pptx", ".wav", ".mp3", ".m4a", ".flac", ".pdf", ".docx"]. IT DOES NOT HANDLE IMAGES.
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`

Available commands (matching Gemini CLI tool signatures):
- `read_file`: Reads and returns the content of a specified file from the local filesystem. Handles text, images, and PDF files. For text files, it can read specific line ranges.
- `write_file`: Writes content to a specified file in the local filesystem. Creates new files or overwrites existing ones.
- `replace`: Replaces text within a file. By default, replaces a single occurrence, but can replace multiple occurrences when `expected_replacements` is specified.
- `list_directory`: Lists the names of files and subdirectories directly within a specified directory path. Can optionally ignore entries matching provided glob patterns.

Before using this tool:
1. Use the read_file or list_directory commands to understand the file's contents and context
2. Verify the directory path is correct when creating new files
3. Always use absolute file paths (starting with /)

When making edits:
   - Ensure the edit results in idiomatic, correct code
   - Do not leave the code in a broken state
   - For replace operations, include sufficient context (3-5 lines) before and after the target text

CRITICAL REQUIREMENTS FOR USING THE REPLACE COMMAND:

1. EXACT MATCHING: The `old_string` parameter must match EXACTLY one or more consecutive lines from the file, including all whitespace and indentation.

2. UNIQUENESS: The `old_string` must uniquely identify a single instance in the file unless `expected_replacements` is specified.

3. REPLACEMENT: The `new_string` parameter should contain the edited lines that replace the `old_string`.

4. MULTIPLE REPLACEMENTS: Use `expected_replacements` parameter when you want to replace multiple occurrences of the same text.

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.
"""

_SHORT_GEMINI_EDITOR_DESCRIPTION = """Gemini-style editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* Based on official Google Gemini CLI tools with exact tool signature matching
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* Provides read_file, write_file, replace, and list_directory commands matching Gemini CLI
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
                        'description': "The absolute path to the file to read (e.g., '/home/user/project/file.txt'). Relative paths are not supported. You must provide an absolute path. Required for read_file command.",
                        'type': 'string',
                        'pattern': '^/',
                    },
                    'offset': {
                        'description': "Optional: For text files, the 0-based line number to start reading from. Requires 'limit' to be set. Use for paginating through large files. For read_file command.",
                        'type': 'number',
                    },
                    'limit': {
                        'description': "Optional: For text files, maximum number of lines to read. Use with 'offset' to paginate through large files. If omitted, reads the entire file (if feasible, up to a default limit). For read_file command.",
                        'type': 'number',
                    },
                    # write_file parameters (matching WriteFileTool from Gemini CLI)
                    'file_path': {
                        'description': "The absolute path to the file to write to (e.g., '/home/user/project/file.txt'). Relative paths are not supported. Required for write_file and replace commands.",
                        'type': 'string',
                    },
                    'content': {
                        'description': 'The content to write to the file. Required for write_file command.',
                        'type': 'string',
                    },
                    # replace parameters (matching EditTool from Gemini CLI)
                    'old_string': {
                        'description': 'The exact literal text to replace, preferably unescaped. For single replacements (default), include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. For multiple replacements, specify expected_replacements parameter. If this string is not the exact literal text (i.e. you escaped it) or does not match exactly, the tool will fail. Required for replace command.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'The exact literal text to replace `old_string` with, preferably unescaped. Provide the EXACT text. Ensure the resulting code is correct and idiomatic. Required for replace command.',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'description': 'Number of replacements expected. Defaults to 1 if not specified. Use when you want to replace multiple occurrences. For replace command.',
                        'type': 'number',
                        'minimum': 1,
                    },
                    # list_directory parameters (matching LSTool from Gemini CLI)
                    'path': {
                        'description': 'The absolute path to the directory to list (must be absolute, not relative). Required for list_directory command.',
                        'type': 'string',
                    },
                    'ignore': {
                        'description': 'List of glob patterns to ignore. Optional for list_directory command.',
                        'items': {
                            'type': 'string',
                        },
                        'type': 'array',
                    },
                    'respect_git_ignore': {
                        'description': 'Optional: Whether to respect .gitignore patterns when listing files. Only available in git repositories. Defaults to true. For list_directory command.',
                        'type': 'boolean',
                    },
                },
                'required': ['command'],
            },
        ),
    )
