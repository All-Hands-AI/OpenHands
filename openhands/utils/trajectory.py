"""Utility functions for processing and formatting trajectories.
Original code from: https://github.com/SWE-Gym/SWE-Gym/blob/main/scripts/openhands-verifier/aggregate_stats_pass_at_n.ipynb
"""

import json


def _convert_content(content) -> str:
    ret = ''
    if isinstance(content, list):
        for item in content:
            assert item['type'] == 'text', 'Only text is supported for now'
            ret += f'{item["text"]}\n'
    else:
        assert isinstance(content, str), 'Only str is supported for now'
        ret = content
    return ret


def _convert_tool_call_to_string(tool_call) -> str:
    """Convert tool call to content in string format."""
    if 'function' not in tool_call:
        raise ValueError("Tool call must contain 'function' key.")
    if 'id' not in tool_call:
        raise ValueError("Tool call must contain 'id' key.")
    if 'type' not in tool_call:
        raise ValueError("Tool call must contain 'type' key.")
    if tool_call['type'] != 'function':
        raise ValueError("Tool call type must be 'function'.")

    ret = f"<function={tool_call['function']['name']}>\n"
    try:
        args = json.loads(tool_call['function']['arguments'])
    except json.JSONDecodeError as e:
        raise ValueError(
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


def format_trajectory(traj: list[dict]) -> str:
    output = ''
    system_message = None

    # Handle system message if present
    if traj[0]['role'] == 'system':
        system_message = traj[0]
        traj = traj[1:]
        content = _convert_content(system_message['content'])
        output += "*** System Message that describes the assistant's behavior ***\n"
        output += f'{content}\n'

    # Merge consecutive user messages first
    merged_traj = []
    current_messages = []

    for i, message in enumerate(traj):
        if message['role'] == 'user':
            current_messages.append(message)
        else:
            if current_messages:
                # Merge all accumulated user messages into one
                merged_content = '\n'.join(
                    _convert_content(msg['content']) for msg in current_messages
                )
                merged_traj.append({'role': 'user', 'content': merged_content})
                current_messages = []
            merged_traj.append(message)

    # Don't forget to handle any remaining user messages
    if current_messages:
        merged_content = '\n'.join(
            _convert_content(msg['content']) for msg in current_messages
        )
        merged_traj.append({'role': 'user', 'content': merged_content})

    # Now process the merged trajectory
    for i, message in enumerate(merged_traj):
        role = message['role']
        content_: str | list = message['content']
        content = _convert_content(content_) if isinstance(content_, list) else content_
        turn_id = i // 2 + 1
        output += '-' * 100 + '\n'
        output += f'*** Turn {turn_id} - {role.upper() if role != "tool" else "TOOL EXECUTION RESULT"} ***\n'

        if role == 'user':
            output += f'{content}\n'
        elif role == 'tool':
            output += f'{content}\n'
        elif role == 'assistant':
            output += f'{content}\n'
            if (
                'tool_calls' in message
                and message['tool_calls'] is not None
                and len(message['tool_calls']) > 0
            ):
                for toolcall_id, tool_call in enumerate(message['tool_calls']):
                    output += f'### Tool Call {toolcall_id}\n'
                    output += f'{_convert_tool_call_to_string(tool_call)}\n'
        else:
            raise ValueError(f'Unexpected role: {role}')

    output += '-' * 100 + '\n'
    return output
