# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gemini editing tools for OpenHands.

This module provides tool specifications that match the Google Gemini CLI editing tools exactly.
The tools are designed to be used with function calling and are translated to OpenHands actions
via the function calling translation layer.

Original code from: https://github.com/google-gemini/gemini-cli
"""

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk


def create_gemini_read_file_tool(detailed: bool = True) -> ChatCompletionToolParam:
    """Create the Gemini ReadFile tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification matching Gemini CLI ReadFile tool
    """
    description = (
        'Reads and returns the content of a specified file from the local filesystem. Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), and PDF files. For text files, it can read specific line ranges.'
        if detailed
        else 'Read file content with optional line range'
    )

    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='read_file',
            description=description,
            parameters={
                'type': 'object',
                'properties': {
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
                },
                'required': ['absolute_path'],
            },
        ),
    )


def create_gemini_write_file_tool(detailed: bool = True) -> ChatCompletionToolParam:
    """Create the Gemini WriteFile tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification matching Gemini CLI WriteFile tool
    """
    description = (
        'Writes content to a specified file in the local filesystem. \n      \n      '
        'The user has the ability to modify `content`. If modified, this will be stated in the response.'
        if detailed
        else 'Write content to a file'
    )

    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='write_file',
            description=description,
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


def create_gemini_replace_tool(detailed: bool = True) -> ChatCompletionToolParam:
    """Create the Gemini Replace (Edit) tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification matching Gemini CLI Edit tool
    """
    description = (
        "Replaces text within a file. By default, replaces a single occurrence, but can replace multiple occurrences when `expected_replacements` is specified. This tool requires providing significant context around the change to ensure precise targeting. Always use the read_file tool to examine the file's current content before attempting a text replacement.\n\n      "
        'The user has the ability to modify the `new_string` content. If modified, this will be stated in the response.\n\n'
        'Expectation for required parameters:\n'
        '1. `file_path` MUST be an absolute path; otherwise an error will be thrown.\n'
        '2. `old_string` MUST be the exact literal text to replace (including all whitespace, indentation, newlines, and surrounding code etc.).\n'
        '3. `new_string` MUST be the exact literal text to replace `old_string` with (also including all whitespace, indentation, newlines, and surrounding code etc.). Ensure the resulting code is correct and idiomatic.\n'
        '4. NEVER escape `old_string` or `new_string`, that would break the exact literal text requirement.\n'
        '**Important:** If ANY of the above are not satisfied, the tool will fail. CRITICAL for `old_string`: Must uniquely identify the single instance to change. Include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. If this string matches multiple locations, or does not match exactly, the tool will fail.\n'
        '**Multiple replacements:** Set `expected_replacements` to the number of occurrences you want to replace. The tool will replace ALL occurrences that match `old_string` exactly. Ensure the number of replacements matches your expectation.'
        if detailed
        else 'Replace text within a file with precise targeting'
    )

    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='replace',
            description=description,
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
                        'description': 'Number of replacements expected. Defaults to 1 if not specified. Use when you want to replace multiple occurrences.',
                        'type': 'number',
                        'minimum': 1,
                    },
                },
                'required': ['file_path', 'old_string', 'new_string'],
            },
        ),
    )


def create_gemini_list_directory_tool(detailed: bool = True) -> ChatCompletionToolParam:
    """Create the Gemini ListDirectory (ReadFolder) tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification matching Gemini CLI ReadFolder tool
    """
    description = (
        'Lists the names of files and subdirectories directly within a specified directory path. Can optionally ignore entries matching provided glob patterns.'
        if detailed
        else 'List directory contents with optional filtering'
    )

    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='list_directory',
            description=description,
            parameters={
                'type': 'object',
                'properties': {
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
                'required': ['path'],
            },
        ),
    )
