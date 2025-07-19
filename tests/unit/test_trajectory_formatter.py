import pytest
from litellm import ChatCompletionMessageToolCall

from openhands.core.message import Message, TextContent
from openhands.utils.trajectory import format_trajectory


# Helper function to create a mock ChatCompletionMessageToolCall
def create_mock_tool_call(name: str, arguments: str):
    return ChatCompletionMessageToolCall(
        function={'name': name, 'arguments': arguments}
    )


def test_empty_trajectory():
    traj = []
    assert (
        format_trajectory(traj)
        == """----------------------------------------------------------------------------------------------------
"""
    )


def test_system_message_only():
    traj = [
        Message(
            role='system', content=[TextContent(text='System behavior description.')]
        )
    ]
    expected_output = """*** System Message that describes the assistant's behavior ***
System behavior description.
----------------------------------------------------------------------------------------------------
"""
    assert format_trajectory(traj) == expected_output


def test_user_messages_only():
    traj = [
        Message(
            role='user',
            content=[TextContent(text='Hello.'), TextContent(text='How are you?')],
        )
    ]
    expected_output = """----------------------------------------------------------------------------------------------------
*** Turn 1 - USER ***
Hello.
How are you?
----------------------------------------------------------------------------------------------------
"""
    assert format_trajectory(traj) == expected_output


def test_mixed_messages():
    traj = [
        Message(
            role='system', content=[TextContent(text='System behavior description.')]
        ),
        Message(role='user', content=[TextContent(text='Hello.')]),
        Message(role='assistant', content=[TextContent(text='Hi there!')]),
        Message(role='user', content=[TextContent(text='你好')]),
        Message(role='assistant', content=[TextContent(text='你好')]),
    ]
    expected_output = """*** System Message that describes the assistant's behavior ***
System behavior description.
----------------------------------------------------------------------------------------------------
*** Turn 1 - USER ***
Hello.
----------------------------------------------------------------------------------------------------
*** Turn 1 - ASSISTANT ***
Hi there!
----------------------------------------------------------------------------------------------------
*** Turn 2 - USER ***
你好
----------------------------------------------------------------------------------------------------
*** Turn 2 - ASSISTANT ***
你好
----------------------------------------------------------------------------------------------------
"""
    assert format_trajectory(traj) == expected_output


def test_tool_call_handling():
    tool_call = create_mock_tool_call(
        name='fn', arguments='{"param1": "value1", "param2": "value2"}'
    )
    traj = [
        Message(
            role='assistant',
            content=[TextContent(text='Running the tool.')],
            tool_calls=[tool_call],
        )
    ]
    expected_output = """----------------------------------------------------------------------------------------------------
*** Turn 1 - ASSISTANT ***
Running the tool.
### Tool Call 0
<function=fn>
<parameter=param1>value1</parameter>
<parameter=param2>value2</parameter>
</function>
----------------------------------------------------------------------------------------------------
"""
    print(format_trajectory(traj))
    assert format_trajectory(traj) == expected_output


def test_invalid_tool_call():
    tool_call = create_mock_tool_call(name='fn', arguments='invalid json')
    traj = [
        Message(
            role='assistant',
            content=[TextContent(text='Running the tool.')],
            tool_calls=[tool_call],
        )
    ]
    with pytest.raises(ValueError, match='Failed to parse arguments as JSON'):
        format_trajectory(traj)
