# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0
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
#
# This file incorporates code from the Google Gemini CLI project
# (https://github.com/google-gemini/gemini-cli), which is licensed
# under the Apache License 2.0.

"""
Gemini ReadFile tool implementation.

This tool provides file reading capabilities that match the Google Gemini CLI
ReadFile tool exactly, including parameter names, types, and descriptions.
"""

from typing import Any


def create_gemini_read_file_tool(detailed: bool = True) -> dict[str, Any]:
    """Create the Gemini ReadFile tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification dictionary matching Gemini CLI ReadFile tool
    """
    description = (
        'Reads and returns the content of a specified file from the local filesystem. '
        'Handles text, images (PNG, JPG, GIF, WEBP, SVG, BMP), and PDF files. '
        'For text files, it can read specific line ranges.'
        if detailed
        else 'Read file content with optional line range support'
    )

    return dict(
        type='function',
        function=dict(
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
