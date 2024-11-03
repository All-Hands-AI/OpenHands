"""Convert function calling messages to non-function calling messages and vice versa.

This will inject prompts so that models that doesn't support function calling
can still be used with function calling agents.

We follow format from: https://docs.litellm.ai/docs/completion/function_call
"""

import copy
import json
import re
from typing import Iterable

from litellm import ChatCompletionToolParam

from openhands.core.exceptions import (
    FunctionCallConversionError,
    FunctionCallValidationError,
)

# Inspired by: https://docs.together.ai/docs/llama-3-function-calling#function-calling-w-llama-31-70b
SYSTEM_PROMPT_SUFFIX_TEMPLATE = """
You have access to the following functions:

{description}

If you choose to call a function ONLY reply in the following format with NO suffix:

<function=example_function_name>
<parameter=example_parameter_1>value_1</parameter>
<parameter=example_parameter_2>
This is the value for the second parameter
that can span
multiple lines
</parameter>
</function>

<IMPORTANT>
Reminder:
- Function calls MUST follow the specified format, start with <function= and end with </function>
- Required parameters MUST be specified
- Only call one function at a time
- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT after.
- If there is no function call available, answer the question like normal with your current knowledge and do not tell the user about function calls
"""

# Regex patterns for function call parsing
FN_REGEX_PATTERN = r'<function=([^>]+)>\n(.*?)</function>'
FN_PARAM_REGEX_PATTERN = r'<parameter=([^>]+)>(.*?)</parameter>'

# Add new regex pattern for tool execution results
TOOL_RESULT_REGEX_PATTERN = r'EXECUTION RESULT of \[(.*?)\]:\n(.*)'


def convert_tool_call_to_string(tool_call: dict) -> str:
    """Convert tool call to content in string format."""
    if 'function' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'function' key.")
    if 'id' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'id' key.")
    if 'type' not in tool_call:
        raise FunctionCallConversionError("Tool call must contain 'type' key.")
    if tool_call['type'] != 'function':
        raise FunctionCallConversionError("Tool call type must be 'function'.")

    ret = f"<function={tool_call['function']['name']}>\n"
    try:
        args = json.loads(tool_call['function']['arguments'])
    except json.JSONDecodeError as e:
        raise FunctionCallConversionError(
            f"Failed to parse arguments as JSON. Arguments: {tool_call['function']['arguments']}"
        ) from e
    for param_name, param_value in args.items():
        is_multiline = isinstance(param_value, str) and '\n' in param_value
        ret += f'<parameter={param_name}>'
        if is_multiline:
            ret += '\n'
        ret += f'{param_value}'
        if is_multiline:
            ret += '\n'
        ret += '</parameter>\n'
    ret += '</function>'
    return ret


def convert_tools_to_description(tools: list[dict]) -> str:
    ret = ''
    for i, tool in enumerate(tools):
        assert tool['type'] == 'function'
        fn = tool['function']
        if i > 0:
            ret += '\n'
        ret += f"---- BEGIN FUNCTION #{i+1}: {fn['name']} ----\n"
        ret += f"Description: {fn['description']}\n"
        if 'parameters' in fn:
            ret += f"Parameters: {json.dumps(fn['parameters'], indent=2)}\n"
        else:
            ret += 'No parameters are required for this function.\n'
        ret += f'---- END FUNCTION #{i+1} ----\n'
    return ret


def convert_fncall_messages_to_non_fncall_messages(
    messages: list[dict],
    tools: list[ChatCompletionToolParam],
) -> list[dict]:
    """Convert function calling messages to non-function calling messages."""
    messages = copy.deepcopy(messages)

    formatted_tools = convert_tools_to_description(tools)
    system_prompt_suffix = SYSTEM_PROMPT_SUFFIX_TEMPLATE.format(
        description=formatted_tools
    )

    converted_messages = []
    for message in messages:
        role, content = message['role'], message['content']
        if content is None:
            content = ''

        # 1. SYSTEM MESSAGES
        # append system prompt suffix to content
        if role == 'system':
            if isinstance(content, str):
                content += system_prompt_suffix
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    content[-1]['text'] += system_prompt_suffix
                else:
                    content.append({'type': 'text', 'text': system_prompt_suffix})
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )
            converted_messages.append({'role': 'system', 'content': content})
        # 2. USER MESSAGES (no change)
        elif role == 'user':
            converted_messages.append(message)

        # 3. ASSISTANT MESSAGES
        # - 3.1 no change if no function call
        # - 3.2 change if function call
        elif role == 'assistant':
            if 'tool_calls' in message and message['tool_calls'] is not None:
                if len(message['tool_calls']) != 1:
                    raise FunctionCallConversionError(
                        f'Expected exactly one tool call in the message. More than one tool call is not supported. But got {len(message["tool_calls"])} tool calls. Content: {content}'
                    )
                try:
                    tool_content = convert_tool_call_to_string(message['tool_calls'][0])
                except FunctionCallConversionError as e:
                    raise FunctionCallConversionError(
                        f'Failed to convert tool call to string. Raw messages: {json.dumps(messages, indent=2)}'
                    ) from e
                if isinstance(content, str):
                    content += '\n\n' + tool_content
                    content = content.lstrip()
                elif isinstance(content, list):
                    if content and content[-1]['type'] == 'text':
                        content[-1]['text'] += '\n\n' + tool_content
                        content[-1]['text'] = content[-1]['text'].lstrip()
                    else:
                        content.append({'type': 'text', 'text': tool_content})
                else:
                    raise FunctionCallConversionError(
                        f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                    )
            converted_messages.append({'role': 'assistant', 'content': content})
        # 4. TOOL MESSAGES (tool outputs)
        elif role == 'tool':
            # Convert tool result as assistant message
            prefix = f'EXECUTION RESULT of [{message["name"]}]:\n'
            # and omit "tool_call_id" AND "name"
            if isinstance(content, str):
                content = prefix + content
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    content[-1]['text'] = prefix + content[-1]['text']
                else:
                    content = [{'type': 'text', 'text': prefix}] + content
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )
            converted_messages.append({'role': 'user', 'content': content})
        else:
            raise FunctionCallConversionError(
                f'Unexpected role {role}. Expected system, user, assistant or tool.'
            )
    return converted_messages


def _extract_and_validate_params(
    matching_tool: dict, param_matches: Iterable[re.Match], fn_name: str
) -> dict:
    params = {}
    # Parse and validate parameters
    required_params = set()
    if 'parameters' in matching_tool and 'required' in matching_tool['parameters']:
        required_params = set(matching_tool['parameters'].get('required', []))

    allowed_params = set()
    if 'parameters' in matching_tool and 'properties' in matching_tool['parameters']:
        allowed_params = set(matching_tool['parameters']['properties'].keys())

    param_name_to_type = {}
    if 'parameters' in matching_tool and 'properties' in matching_tool['parameters']:
        param_name_to_type = {
            name: val.get('type', 'string')
            for name, val in matching_tool['parameters']['properties'].items()
        }

    # Collect parameters
    found_params = set()
    for param_match in param_matches:
        param_name = param_match.group(1)
        param_value = param_match.group(2).strip()

        # Validate parameter is allowed
        if allowed_params and param_name not in allowed_params:
            raise FunctionCallValidationError(
                f"Parameter '{param_name}' is not allowed for function '{fn_name}'. "
                f'Allowed parameters: {allowed_params}'
            )

        # Validate and convert parameter type
        # supported: string, integer, array
        if param_name in param_name_to_type:
            if param_name_to_type[param_name] == 'integer':
                try:
                    param_value = int(param_value)
                except ValueError:
                    raise FunctionCallValidationError(
                        f"Parameter '{param_name}' is expected to be an integer."
                    )
            elif param_name_to_type[param_name] == 'array':
                try:
                    param_value = json.loads(param_value)
                except json.JSONDecodeError:
                    raise FunctionCallValidationError(
                        f"Parameter '{param_name}' is expected to be an array."
                    )
            else:
                # string
                pass

        # Enum check
        if 'enum' in matching_tool['parameters']['properties'][param_name]:
            if (
                param_value
                not in matching_tool['parameters']['properties'][param_name]['enum']
            ):
                raise FunctionCallValidationError(
                    f"Parameter '{param_name}' is expected to be one of {matching_tool['parameters']['properties'][param_name]['enum']}."
                )

        params[param_name] = param_value
        found_params.add(param_name)

    # Check all required parameters are present
    missing_params = required_params - found_params
    if missing_params:
        raise FunctionCallValidationError(
            f"Missing required parameters for function '{fn_name}': {missing_params}"
        )
    return params


def convert_non_fncall_messages_to_fncall_messages(
    messages: list[dict],
    tools: list[ChatCompletionToolParam],
) -> list[dict]:
    """Convert non-function calling messages back to function calling messages."""
    messages = copy.deepcopy(messages)
    formatted_tools = convert_tools_to_description(tools)
    system_prompt_suffix = SYSTEM_PROMPT_SUFFIX_TEMPLATE.format(
        description=formatted_tools
    )

    converted_messages = []
    tool_call_counter = 1  # Counter for tool calls

    for message in messages:
        role, content = message['role'], message['content']

        # For system messages, remove the added suffix
        if role == 'system':
            if isinstance(content, str):
                # Remove the suffix if present
                content = content.split(system_prompt_suffix)[0]
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    # Remove the suffix from the last text item
                    content[-1]['text'] = content[-1]['text'].split(
                        system_prompt_suffix
                    )[0]
            converted_messages.append({'role': 'system', 'content': content})
        # Skip user messages (no conversion needed)
        elif role == 'user':
            # Check for tool execution result pattern
            if isinstance(content, str):
                tool_result_match = re.search(
                    TOOL_RESULT_REGEX_PATTERN, content, re.DOTALL
                )
            elif isinstance(content, list):
                tool_result_match = next(
                    (
                        _match
                        for item in content
                        if item.get('type') == 'text'
                        and (
                            _match := re.search(
                                TOOL_RESULT_REGEX_PATTERN, item['text'], re.DOTALL
                            )
                        )
                    ),
                    None,
                )
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )

            if tool_result_match:
                if not (
                    isinstance(content, str)
                    or (
                        isinstance(content, list)
                        and len(content) == 1
                        and content[0].get('type') == 'text'
                    )
                ):
                    raise FunctionCallConversionError(
                        f'Expected str or list with one text item when tool result is present in the message. Content: {content}'
                    )
                tool_name = tool_result_match.group(1)
                tool_result = tool_result_match.group(2).strip()

                # Convert to tool message format
                converted_messages.append(
                    {
                        'role': 'tool',
                        'name': tool_name,
                        'content': [{'type': 'text', 'text': tool_result}]
                        if isinstance(content, list)
                        else tool_result,
                        'tool_call_id': f'toolu_{tool_call_counter-1:02d}',  # Use last generated ID
                    }
                )
            else:
                converted_messages.append(message)

        # Handle assistant messages
        elif role == 'assistant':
            if isinstance(content, str):
                fn_match = re.search(FN_REGEX_PATTERN, content, re.DOTALL)
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    fn_match = re.search(
                        FN_REGEX_PATTERN, content[-1]['text'], re.DOTALL
                    )
                else:
                    fn_match = None
                fn_match_exists = any(
                    item.get('type') == 'text'
                    and re.search(FN_REGEX_PATTERN, item['text'], re.DOTALL)
                    for item in content
                )
                if fn_match_exists and not fn_match:
                    raise FunctionCallConversionError(
                        f'Expecting function call in the LAST index of content list. But got content={content}'
                    )
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )

            if fn_match:
                fn_name = fn_match.group(1)
                fn_body = fn_match.group(2)
                matching_tool = next(
                    (
                        tool['function']
                        for tool in tools
                        if tool['type'] == 'function'
                        and tool['function']['name'] == fn_name
                    ),
                    None,
                )
                # Validate function exists in tools
                if not matching_tool:
                    raise FunctionCallValidationError(
                        f"Function '{fn_name}' not found in available tools: {[tool['function']['name'] for tool in tools if tool['type'] == 'function']}"
                    )

                # Parse parameters
                param_matches = re.finditer(FN_PARAM_REGEX_PATTERN, fn_body, re.DOTALL)
                params = _extract_and_validate_params(
                    matching_tool, param_matches, fn_name
                )

                # Create tool call with unique ID
                tool_call_id = f'toolu_{tool_call_counter:02d}'
                tool_call = {
                    'index': 1,  # always 1 because we only support **one tool call per message**
                    'id': tool_call_id,
                    'type': 'function',
                    'function': {'name': fn_name, 'arguments': json.dumps(params)},
                }
                tool_call_counter += 1  # Increment counter

                # Remove the function call part from content
                if isinstance(content, list):
                    assert content and content[-1]['type'] == 'text'
                    content[-1]['text'] = (
                        content[-1]['text'].split('<function=')[0].strip()
                    )
                elif isinstance(content, str):
                    content = content.split('<function=')[0].strip()
                else:
                    raise FunctionCallConversionError(
                        f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                    )

                converted_messages.append(
                    {'role': 'assistant', 'content': content, 'tool_calls': [tool_call]}
                )
            else:
                # No function call, keep message as is
                converted_messages.append(message)

        else:
            raise FunctionCallConversionError(
                f'Unexpected role {role}. Expected system, user, or assistant in non-function calling messages.'
            )
    return converted_messages


def convert_from_multiple_tool_calls_to_single_tool_call_messages(
    messages: list[dict],
) -> list[dict]:
    """Break one message with multiple tool calls into multiple messages."""
    converted_messages = []

    pending_tool_calls: dict[str, dict] = {}
    for message in messages:
        role, content = message['role'], message['content']
        if role == 'assistant':
            if message.get('tool_calls') and len(message['tool_calls']) > 1:
                # handle multiple tool calls by breaking them into multiple messages
                for i, tool_call in enumerate(message['tool_calls']):
                    pending_tool_calls[tool_call['id']] = {
                        'role': 'assistant',
                        'content': content if i == 0 else '',
                        'tool_calls': [tool_call],
                    }
            else:
                converted_messages.append(message)
        elif role == 'tool':
            if message['tool_call_id'] in pending_tool_calls:
                # remove the tool call from the pending list
                _tool_call_message = pending_tool_calls.pop(message['tool_call_id'])
                converted_messages.append(_tool_call_message)
                # add the tool result
                converted_messages.append(message)
            else:
                assert (
                    len(pending_tool_calls) == 0
                ), f'Found pending tool calls but not found in pending list: {pending_tool_calls=}'
                converted_messages.append(message)
        else:
            assert (
                len(pending_tool_calls) == 0
            ), f'Found pending tool calls but not expect to handle it with role {role}: {pending_tool_calls=}, {message=}'
            converted_messages.append(message)

    if len(pending_tool_calls) > 0:
        raise FunctionCallConversionError(
            f'Found pending tool calls but no tool result: {pending_tool_calls=}'
        )
    return converted_messages
