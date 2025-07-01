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
Gemini ListDirectory tool implementation.

This tool provides directory listing capabilities that match the Google Gemini CLI
LS tool exactly, including parameter names, types, and descriptions.
"""

from typing import Any


def create_gemini_list_directory_tool(detailed: bool = True) -> dict[str, Any]:
    """Create the Gemini ListDirectory tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification dictionary matching Gemini CLI LS tool
    """
    description = (
        'Lists the names of files and subdirectories directly within a specified directory path. '
        'Can optionally ignore entries matching provided glob patterns.'
        if detailed
        else 'List directory contents with optional filtering'
    )

    return dict(
        type='function',
        function=dict(
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
