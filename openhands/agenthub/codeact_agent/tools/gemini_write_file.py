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
Gemini WriteFile tool implementation.

This tool provides file writing capabilities that match the Google Gemini CLI
WriteFile tool exactly, including parameter names, types, and descriptions.
"""

from typing import Any


def create_gemini_write_file_tool(detailed: bool = True) -> dict[str, Any]:
    """Create the Gemini WriteFile tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification dictionary matching Gemini CLI WriteFile tool
    """
    description = (
        'Writes content to a specified file in the local filesystem. \n      \n      '
        'The user has the ability to modify `content`. If modified, this will be stated in the response.'
        if detailed
        else 'Write content to a file'
    )

    return dict(
        type='function',
        function=dict(
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
