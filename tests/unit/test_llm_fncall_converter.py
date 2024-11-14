"""Test for FunctionCallingConverter."""

import copy
import json

import pytest
from litellm import ChatCompletionToolParam

from openhands.llm.fn_call_converter import (
    IN_CONTEXT_LEARNING_EXAMPLE_PREFIX,
    IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX,
    FunctionCallConversionError,
    convert_fncall_messages_to_non_fncall_messages,
    convert_from_multiple_tool_calls_to_single_tool_call_messages,
    convert_non_fncall_messages_to_fncall_messages,
    convert_tool_call_to_string,
    convert_tools_to_description,
)

FNCALL_TOOLS: list[ChatCompletionToolParam] = [
    {
        'type': 'function',
        'function': {
            'name': 'execute_bash',
            'description': 'Execute a bash command in the terminal.\n* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.\n* Interactive: If a bash command returns exit code `-1`, this means the process is not yet finished. The assistant must then send a second call to terminal with an empty `command` (which will retrieve any additional logs), or it can send additional text (set `command` to the text) to STDIN of the running process, or it can send command=`ctrl+c` to interrupt the process.\n* Timeout: If a command execution result says "Command timed out. Sending SIGINT to the process", the assistant should retry running the command in the background.\n',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': 'The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.',
                    }
                },
                'required': ['command'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'finish',
            'description': 'Finish the interaction when the task is complete OR if the assistant cannot proceed further with the task.',
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'str_replace_editor',
            'description': 'Custom editing tool for viewing, creating and editing files\n* State is persistent across command calls and discussions with the user\n* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n* The `create` command cannot be used if the specified `path` already exists as a file\n* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`\n* The `undo_edit` command will revert the last edit made to the file at `path`\n\nNotes for using the `str_replace` command:\n* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n* The `new_str` parameter should contain the edited lines that should replace the `old_str`\n',
            'parameters': {
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
                        'description': 'Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.',
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
        },
    },
]


def test_convert_tools_to_description():
    formatted_tools = convert_tools_to_description(FNCALL_TOOLS)
    print(formatted_tools)
    assert (
        formatted_tools.strip()
        == """---- BEGIN FUNCTION #1: execute_bash ----
Description: Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.
* Interactive: If a bash command returns exit code `-1`, this means the process is not yet finished. The assistant must then send a second call to terminal with an empty `command` (which will retrieve any additional logs), or it can send additional text (set `command` to the text) to STDIN of the running process, or it can send command=`ctrl+c` to interrupt the process.
* Timeout: If a command execution result says "Command timed out. Sending SIGINT to the process", the assistant should retry running the command in the background.

Parameters:
  (1) command (string, required): The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.
---- END FUNCTION #1 ----

---- BEGIN FUNCTION #2: finish ----
Description: Finish the interaction when the task is complete OR if the assistant cannot proceed further with the task.
No parameters are required for this function.
---- END FUNCTION #2 ----

---- BEGIN FUNCTION #3: str_replace_editor ----
Description: Custom editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`

Parameters:
  (1) command (string, required): The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.
Allowed values: [`view`, `create`, `str_replace`, `insert`, `undo_edit`]
  (2) path (string, required): Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.
  (3) file_text (string, optional): Required parameter of `create` command, with the content of the file to be created.
  (4) old_str (string, optional): Required parameter of `str_replace` command containing the string in `path` to replace.
  (5) new_str (string, optional): Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.
  (6) insert_line (integer, optional): Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.
  (7) view_range (array, optional): Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.
---- END FUNCTION #3 ----""".strip()
    )


FNCALL_MESSAGES = [
    {
        'content': [
            {
                'type': 'text',
                'text': "You are a helpful assistant that can interact with a computer to solve tasks.\n<IMPORTANT>\n* If user provides a path, you should NOT assume it's relative to the current working directory. Instead, you should explore the file system to find the file before working on it.\n</IMPORTANT>\n\n",
                'cache_control': {'type': 'ephemeral'},
            }
        ],
        'role': 'system',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "<uploaded_files>\n/workspace/astropy__astropy__5.1\n</uploaded_files>\nI've uploaded a python code repository in the directory astropy__astropy__5.1. LONG DESCRIPTION:\n\n",
            }
        ],
        'role': 'user',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "I'll help you implement the necessary changes to meet the requirements. Let's follow the steps:\n\n1. First, let's explore the repository structure:",
            }
        ],
        'role': 'assistant',
        'tool_calls': [
            {
                'index': 1,
                'function': {
                    'arguments': '{"command": "ls -la /workspace/astropy__astropy__5.1"}',
                    'name': 'execute_bash',
                },
                'id': 'toolu_01',
                'type': 'function',
            }
        ],
    },
    {
        'content': [
            {
                'type': 'text',
                'text': 'ls -la /workspace/astropy__astropy__5.1\r\nls: /workspace/astropy__astropy__5.1: Bad file descriptor\r\nlrwxrwxrwx 1 root root 8 Oct 28 21:58 /workspace/astropy__astropy__5.1 -> /testbed[Python Interpreter: /opt/miniconda3/envs/testbed/bin/python]\nroot@openhands-workspace:/workspace/astropy__astropy__5.1 # \n[Command finished with exit code 0]',
            }
        ],
        'role': 'tool',
        'tool_call_id': 'toolu_01',
        'name': 'execute_bash',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "I see there's a symlink. Let's explore the actual directory:",
            }
        ],
        'role': 'assistant',
        'tool_calls': [
            {
                'index': 1,
                'function': {
                    'arguments': '{"command": "ls -la /testbed"}',
                    'name': 'execute_bash',
                },
                'id': 'toolu_02',
                'type': 'function',
            }
        ],
    },
    {
        'content': [
            {
                'type': 'text',
                'text': 'SOME OBSERVATION',
            }
        ],
        'role': 'tool',
        'tool_call_id': 'toolu_02',
        'name': 'execute_bash',
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "Let's look at the source code file mentioned in the PR description:",
            }
        ],
        'role': 'assistant',
        'tool_calls': [
            {
                'index': 1,
                'function': {
                    'arguments': '{"command": "view", "path": "/testbed/astropy/io/fits/card.py"}',
                    'name': 'str_replace_editor',
                },
                'id': 'toolu_03',
                'type': 'function',
            }
        ],
    },
    {
        'content': [
            {
                'type': 'text',
                'text': "Here's the result of running `cat -n` on /testbed/astropy/io/fits/card.py:\n     1\t# Licensed under a 3-clause BSD style license - see PYFITS.rst...VERY LONG TEXT",
            }
        ],
        'role': 'tool',
        'tool_call_id': 'toolu_03',
        'name': 'str_replace_editor',
    },
]

NON_FNCALL_MESSAGES = [
    {
        'role': 'system',
        'content': [
            {
                'type': 'text',
                'text': 'You are a helpful assistant that can interact with a computer to solve tasks.\n<IMPORTANT>\n* If user provides a path, you should NOT assume it\'s relative to the current working directory. Instead, you should explore the file system to find the file before working on it.\n</IMPORTANT>\n\n\nYou have access to the following functions:\n\n---- BEGIN FUNCTION #1: execute_bash ----\nDescription: Execute a bash command in the terminal.\n* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.\n* Interactive: If a bash command returns exit code `-1`, this means the process is not yet finished. The assistant must then send a second call to terminal with an empty `command` (which will retrieve any additional logs), or it can send additional text (set `command` to the text) to STDIN of the running process, or it can send command=`ctrl+c` to interrupt the process.\n* Timeout: If a command execution result says "Command timed out. Sending SIGINT to the process", the assistant should retry running the command in the background.\n\nParameters:\n  (1) command (string, required): The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.\n---- END FUNCTION #1 ----\n\n---- BEGIN FUNCTION #2: finish ----\nDescription: Finish the interaction when the task is complete OR if the assistant cannot proceed further with the task.\nNo parameters are required for this function.\n---- END FUNCTION #2 ----\n\n---- BEGIN FUNCTION #3: str_replace_editor ----\nDescription: Custom editing tool for viewing, creating and editing files\n* State is persistent across command calls and discussions with the user\n* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n* The `create` command cannot be used if the specified `path` already exists as a file\n* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`\n* The `undo_edit` command will revert the last edit made to the file at `path`\n\nNotes for using the `str_replace` command:\n* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n* The `new_str` parameter should contain the edited lines that should replace the `old_str`\n\nParameters:\n  (1) command (string, required): The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.\nAllowed values: [`view`, `create`, `str_replace`, `insert`, `undo_edit`]\n  (2) path (string, required): Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.\n  (3) file_text (string, optional): Required parameter of `create` command, with the content of the file to be created.\n  (4) old_str (string, optional): Required parameter of `str_replace` command containing the string in `path` to replace.\n  (5) new_str (string, optional): Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.\n  (6) insert_line (integer, optional): Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.\n  (7) view_range (array, optional): Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.\n---- END FUNCTION #3 ----\n\n\nIf you choose to call a function ONLY reply in the following format with NO suffix:\n\n<function=example_function_name>\n<parameter=example_parameter_1>value_1</parameter>\n<parameter=example_parameter_2>\nThis is the value for the second parameter\nthat can span\nmultiple lines\n</parameter>\n</function>\n\n<IMPORTANT>\nReminder:\n- Function calls MUST follow the specified format, start with <function= and end with </function>\n- Required parameters MUST be specified\n- Only call one function at a time\n- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT after.\n- If there is no function call available, answer the question like normal with your current knowledge and do not tell the user about function calls\n',
                'cache_control': {'type': 'ephemeral'},
            }
        ],
    },
    {
        'content': [
            {
                'type': 'text',
                'text': IN_CONTEXT_LEARNING_EXAMPLE_PREFIX
                + "<uploaded_files>\n/workspace/astropy__astropy__5.1\n</uploaded_files>\nI've uploaded a python code repository in the directory astropy__astropy__5.1. LONG DESCRIPTION:\n\n"
                + IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX,
            }
        ],
        'role': 'user',
    },
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': "I'll help you implement the necessary changes to meet the requirements. Let's follow the steps:\n\n1. First, let's explore the repository structure:\n\n<function=execute_bash>\n<parameter=command>ls -la /workspace/astropy__astropy__5.1</parameter>\n</function>",
            }
        ],
    },
    {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'EXECUTION RESULT of [execute_bash]:\nls -la /workspace/astropy__astropy__5.1\r\nls: /workspace/astropy__astropy__5.1: Bad file descriptor\r\nlrwxrwxrwx 1 root root 8 Oct 28 21:58 /workspace/astropy__astropy__5.1 -> /testbed[Python Interpreter: /opt/miniconda3/envs/testbed/bin/python]\nroot@openhands-workspace:/workspace/astropy__astropy__5.1 # \n[Command finished with exit code 0]',
            }
        ],
    },
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': "I see there's a symlink. Let's explore the actual directory:\n\n<function=execute_bash>\n<parameter=command>ls -la /testbed</parameter>\n</function>",
            }
        ],
    },
    {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'EXECUTION RESULT of [execute_bash]:\nSOME OBSERVATION',
            }
        ],
    },
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': "Let's look at the source code file mentioned in the PR description:\n\n<function=str_replace_editor>\n<parameter=command>view</parameter>\n<parameter=path>/testbed/astropy/io/fits/card.py</parameter>\n</function>",
            }
        ],
    },
    {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': "EXECUTION RESULT of [str_replace_editor]:\nHere's the result of running `cat -n` on /testbed/astropy/io/fits/card.py:\n     1\t# Licensed under a 3-clause BSD style license - see PYFITS.rst...VERY LONG TEXT",
            }
        ],
    },
]

FNCALL_RESPONSE_MESSAGE = {
    'content': [
        {
            'type': 'text',
            'text': 'Let me search for the `_format_float` method mentioned in the PR description:',
        }
    ],
    'role': 'assistant',
    'tool_calls': [
        {
            'index': 1,
            'function': {
                'arguments': '{"command": "grep -n \\"_format_float\\" /testbed/astropy/io/fits/card.py"}',
                'name': 'execute_bash',
            },
            'id': 'toolu_04',
            'type': 'function',
        }
    ],
}

NON_FNCALL_RESPONSE_MESSAGE = {
    'content': [
        {
            'type': 'text',
            'text': 'Let me search for the `_format_float` method mentioned in the PR description:\n\n<function=execute_bash>\n<parameter=command>grep -n "_format_float" /testbed/astropy/io/fits/card.py</parameter>\n</function>',
        }
    ],
    'role': 'assistant',
}


@pytest.mark.parametrize(
    'tool_calls, expected',
    [
        # Original test case
        (
            FNCALL_RESPONSE_MESSAGE['tool_calls'],
            """<function=execute_bash>
<parameter=command>grep -n "_format_float" /testbed/astropy/io/fits/card.py</parameter>
</function>""",
        ),
        # Test case with multiple parameters
        (
            [
                {
                    'index': 1,
                    'function': {
                        'arguments': '{"command": "view", "path": "/test/file.py", "view_range": [1, 10]}',
                        'name': 'str_replace_editor',
                    },
                    'id': 'test_id',
                    'type': 'function',
                }
            ],
            """<function=str_replace_editor>
<parameter=command>view</parameter>
<parameter=path>/test/file.py</parameter>
<parameter=view_range>[1, 10]</parameter>
</function>""",
        ),
    ],
)
def test_convert_tool_call_to_string(tool_calls, expected):
    assert len(tool_calls) == 1
    converted = convert_tool_call_to_string(tool_calls[0])
    print(converted)
    assert converted == expected


def test_convert_fncall_messages_to_non_fncall_messages():
    converted_non_fncall = convert_fncall_messages_to_non_fncall_messages(
        FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert converted_non_fncall == NON_FNCALL_MESSAGES


def test_convert_non_fncall_messages_to_fncall_messages():
    converted = convert_non_fncall_messages_to_fncall_messages(
        NON_FNCALL_MESSAGES, FNCALL_TOOLS
    )
    print(json.dumps(converted, indent=2))
    assert converted == FNCALL_MESSAGES


def test_two_way_conversion_nonfn_to_fn_to_nonfn():
    non_fncall_copy = copy.deepcopy(NON_FNCALL_MESSAGES)
    converted_fncall = convert_non_fncall_messages_to_fncall_messages(
        NON_FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert (
        non_fncall_copy == NON_FNCALL_MESSAGES
    )  # make sure original messages are not modified
    assert converted_fncall == FNCALL_MESSAGES

    fncall_copy = copy.deepcopy(FNCALL_MESSAGES)
    converted_non_fncall = convert_fncall_messages_to_non_fncall_messages(
        FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert (
        fncall_copy == FNCALL_MESSAGES
    )  # make sure original messages are not modified
    assert converted_non_fncall == NON_FNCALL_MESSAGES


def test_two_way_conversion_fn_to_nonfn_to_fn():
    fncall_copy = copy.deepcopy(FNCALL_MESSAGES)
    converted_non_fncall = convert_fncall_messages_to_non_fncall_messages(
        FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert (
        fncall_copy == FNCALL_MESSAGES
    )  # make sure original messages are not modified
    assert converted_non_fncall == NON_FNCALL_MESSAGES

    non_fncall_copy = copy.deepcopy(NON_FNCALL_MESSAGES)
    converted_fncall = convert_non_fncall_messages_to_fncall_messages(
        NON_FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert (
        non_fncall_copy == NON_FNCALL_MESSAGES
    )  # make sure original messages are not modified
    assert converted_fncall == FNCALL_MESSAGES


def test_infer_fncall_on_noncall_model():
    messages_for_llm_inference = convert_fncall_messages_to_non_fncall_messages(
        FNCALL_MESSAGES, FNCALL_TOOLS
    )
    assert messages_for_llm_inference == NON_FNCALL_MESSAGES
    # Mock LLM inference
    response_message_from_llm_inference = NON_FNCALL_RESPONSE_MESSAGE

    # Convert back to fncall messages to hand back to the agent
    # so agent is model-agnostic
    all_nonfncall_messages = NON_FNCALL_MESSAGES + [response_message_from_llm_inference]
    converted_fncall_messages = convert_non_fncall_messages_to_fncall_messages(
        all_nonfncall_messages, FNCALL_TOOLS
    )
    assert converted_fncall_messages == FNCALL_MESSAGES + [FNCALL_RESPONSE_MESSAGE]
    assert converted_fncall_messages[-1] == FNCALL_RESPONSE_MESSAGE


def test_convert_from_multiple_tool_calls_to_single_tool_call_messages():
    # Test case with multiple tool calls in one message
    input_messages = [
        {
            'role': 'assistant',
            'content': 'Let me help you with that.',
            'tool_calls': [
                {
                    'id': 'call1',
                    'type': 'function',
                    'function': {'name': 'func1', 'arguments': '{}'},
                },
                {
                    'id': 'call2',
                    'type': 'function',
                    'function': {'name': 'func2', 'arguments': '{}'},
                },
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call1',
            'content': 'Result 1',
            'name': 'func1',
        },
        {
            'role': 'tool',
            'tool_call_id': 'call2',
            'content': 'Result 2',
            'name': 'func2',
        },
        {
            'role': 'assistant',
            'content': 'Test again',
            'tool_calls': [
                {
                    'id': 'call3',
                    'type': 'function',
                    'function': {'name': 'func3', 'arguments': '{}'},
                },
                {
                    'id': 'call4',
                    'type': 'function',
                    'function': {'name': 'func4', 'arguments': '{}'},
                },
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call3',
            'content': 'Result 3',
            'name': 'func3',
        },
        {
            'role': 'tool',
            'tool_call_id': 'call4',
            'content': 'Result 4',
            'name': 'func4',
        },
    ]

    expected_output = [
        {
            'role': 'assistant',
            'content': 'Let me help you with that.',
            'tool_calls': [
                {
                    'id': 'call1',
                    'type': 'function',
                    'function': {'name': 'func1', 'arguments': '{}'},
                }
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call1',
            'content': 'Result 1',
            'name': 'func1',
        },
        {
            'role': 'assistant',
            'content': '',
            'tool_calls': [
                {
                    'id': 'call2',
                    'type': 'function',
                    'function': {'name': 'func2', 'arguments': '{}'},
                }
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call2',
            'content': 'Result 2',
            'name': 'func2',
        },
        {
            'role': 'assistant',
            'content': 'Test again',
            'tool_calls': [
                {
                    'id': 'call3',
                    'type': 'function',
                    'function': {'name': 'func3', 'arguments': '{}'},
                }
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call3',
            'content': 'Result 3',
            'name': 'func3',
        },
        {
            'role': 'assistant',
            'content': '',
            'tool_calls': [
                {
                    'id': 'call4',
                    'type': 'function',
                    'function': {'name': 'func4', 'arguments': '{}'},
                }
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call4',
            'content': 'Result 4',
            'name': 'func4',
        },
    ]

    result = convert_from_multiple_tool_calls_to_single_tool_call_messages(
        input_messages
    )
    assert result == expected_output


def test_convert_from_multiple_tool_calls_to_single_tool_call_messages_incomplete():
    # Test case with multiple tool calls in one message
    input_messages = [
        {
            'role': 'assistant',
            'content': 'Let me help you with that.',
            'tool_calls': [
                {
                    'id': 'call1',
                    'type': 'function',
                    'function': {'name': 'func1', 'arguments': '{}'},
                },
                {
                    'id': 'call2',
                    'type': 'function',
                    'function': {'name': 'func2', 'arguments': '{}'},
                },
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call1',
            'content': 'Result 1',
            'name': 'func1',
        },
    ]

    with pytest.raises(FunctionCallConversionError):
        convert_from_multiple_tool_calls_to_single_tool_call_messages(input_messages)


def test_convert_from_multiple_tool_calls_no_changes_needed():
    # Test case where no conversion is needed (single tool call)
    input_messages = [
        {
            'role': 'assistant',
            'content': 'Let me help you with that.',
            'tool_calls': [
                {
                    'id': 'call1',
                    'type': 'function',
                    'function': {'name': 'func1', 'arguments': '{}'},
                }
            ],
        },
        {
            'role': 'tool',
            'tool_call_id': 'call1',
            'content': 'Result 1',
            'name': 'func1',
        },
    ]

    result = convert_from_multiple_tool_calls_to_single_tool_call_messages(
        input_messages
    )
    assert result == input_messages


def test_convert_from_multiple_tool_calls_no_tool_calls():
    # Test case with no tool calls
    input_messages = [
        {'role': 'user', 'content': 'Hello'},
        {'role': 'assistant', 'content': 'Hi there!'},
    ]

    result = convert_from_multiple_tool_calls_to_single_tool_call_messages(
        input_messages
    )
    assert result == input_messages
