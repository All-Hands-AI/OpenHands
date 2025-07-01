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
Gemini Replace (Edit) tool implementation.

This tool provides text replacement capabilities that match the Google Gemini CLI
Edit tool exactly, including parameter names, types, and descriptions.
"""

from typing import Any


def create_gemini_replace_tool(detailed: bool = True) -> dict[str, Any]:
    """Create the Gemini Replace (Edit) tool specification.

    Args:
        detailed: Whether to include detailed descriptions

    Returns:
        Tool specification dictionary matching Gemini CLI Edit tool
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

    return dict(
        type='function',
        function=dict(
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
