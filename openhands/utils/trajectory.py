"""
Utility functions for processing and formatting trajectories.
Original code from: https://github.com/SWE-Gym/SWE-Gym/blob/main/scripts/openhands-verifier/aggregate_stats_pass_at_n.ipynb
"""

import json

from litellm import ChatCompletionMessageToolCall

from openhands.core.message import ImageContent, Message, TextContent


def convert_content(content: list[TextContent | ImageContent]) -> str:
    """Converts a list of message content to a single string."""
    return '\n'.join(item.text for item in content if item.type == 'text')


def convert_tool_call_to_string(tool_call: ChatCompletionMessageToolCall) -> str:
    """Converts tool call arguments to a string representation."""
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        raise ValueError(
            f'Failed to parse arguments as JSON. Arguments: {tool_call["function"]["arguments"]}'
        ) from e

    tool_call_str = f'<function={tool_call.function.name}>\n'
    for param_name, param_value in args.items():
        is_multiline_value = isinstance(param_value, str) and '\n' in param_value
        param_value = '\n' + param_value + '\n' if is_multiline_value else param_value
        tool_call_str += f'<parameter={param_name}>{param_value}</parameter>\n'
    tool_call_str += '</function>'
    return tool_call_str


def merge_user_messages(traj: list[Message]) -> list[Message]:
    """Merges consecutive user messages into a single message."""
    merged_traj = []
    current_messages = []

    for message in traj:
        if message.role == 'user':
            current_messages.append(message)
        else:
            if current_messages:
                merged_content = '\n'.join(
                    convert_content(msg.content) for msg in current_messages
                )
                merged_traj.append(
                    Message(role='user', content=[TextContent(text=merged_content)])
                )
                current_messages = []
            merged_traj.append(message)

    if current_messages:
        merged_content = '\n'.join(
            convert_content(msg.content) for msg in current_messages
        )
        merged_traj.append(
            Message(role='user', content=[TextContent(text=merged_content)])
        )

    return merged_traj


def format_trajectory(traj: list[Message]) -> str:
    """Formats the message trajectory into a human-readable string."""
    output = ''
    system_message = None

    if traj:
        # Handle system message if present
        if traj[0].role == 'system':
            system_message = traj[0]
            traj = traj[1:]
            content = convert_content(system_message.content)
            output += "*** System Message that describes the assistant's behavior ***\n"
            output += f'{content}\n'

    # Merge consecutive user messages
    merged_traj = merge_user_messages(traj)

    # Process the merged trajectory
    for i, message in enumerate(merged_traj):
        role = message.role
        content = convert_content(message.content)
        turn_id = i // 2 + 1
        output += '-' * 100 + '\n'
        output += f'*** Turn {turn_id} - {role.upper() if role != "tool" else "TOOL EXECUTION RESULT"} ***\n'

        if role == 'user' or role == 'tool' or role == 'assistant':
            output += f'{content}\n'
            if role == 'assistant' and message.tool_calls:
                for toolcall_id, tool_call in enumerate(message.tool_calls):
                    output += f'### Tool Call {toolcall_id}\n'
                    output += f'{convert_tool_call_to_string(tool_call)}\n'
        else:
            raise ValueError(f'Unexpected role: {role}')

    output += '-' * 100 + '\n'
    return output
