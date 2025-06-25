"""Test reasoning content handling."""

import json

from litellm import ModelResponse

from openhands.agenthub.codeact_agent.function_calling import response_to_actions
from openhands.events.action import MessageAction


def create_mock_response_with_reasoning(
    content: str, reasoning_content: str | None = None, tool_calls: list | None = None
) -> ModelResponse:
    """Helper function to create a mock response with reasoning content."""
    message = {
        'content': content,
        'role': 'assistant',
        'reasoning_content': reasoning_content,
    }

    if tool_calls:
        message['tool_calls'] = tool_calls

    return ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': message,
                'index': 0,
                'finish_reason': 'stop',
            }
        ],
    )


def test_reasoning_content_preserved_in_message_action():
    """Test that reasoning content is now preserved in MessageAction."""
    reasoning_content = 'Let me think about this step by step. First, I need to understand what the user is asking for...'
    content = "I'll help you with that task."

    response = create_mock_response_with_reasoning(
        content=content, reasoning_content=reasoning_content
    )

    actions = response_to_actions(response)

    # Should have one MessageAction
    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)

    # Content should be preserved
    assert actions[0].content == content

    # Reasoning content should now be preserved
    assert hasattr(actions[0], 'reasoning_content')
    assert actions[0].reasoning_content == reasoning_content


def test_reasoning_content_preserved_with_tool_calls():
    """Test that reasoning content is now preserved when tool calls are present."""
    reasoning_content = (
        'I need to run a command to check the current directory structure.'
    )
    content = 'Let me check the directory structure.'

    tool_calls = [
        {
            'function': {
                'name': 'execute_bash',
                'arguments': json.dumps({'command': 'ls -la'}),
            },
            'id': 'mock-tool-call-id',
            'type': 'function',
        }
    ]

    response = create_mock_response_with_reasoning(
        content=content, reasoning_content=reasoning_content, tool_calls=tool_calls
    )

    actions = response_to_actions(response)

    # Should have one action (CmdRunAction)
    assert len(actions) == 1

    # The reasoning content should now be preserved in the first action
    assert hasattr(actions[0], 'reasoning_content')
    assert actions[0].reasoning_content == reasoning_content


def test_reasoning_content_available_in_litellm_response():
    """Test that reasoning content is available in the LiteLLM response structure.

    This test confirms that the reasoning content is present in the response
    but not being extracted by our code.
    """
    reasoning_content = 'This is the reasoning trace from the LLM.'
    content = 'This is the main response.'

    response = create_mock_response_with_reasoning(
        content=content, reasoning_content=reasoning_content
    )

    # Verify that reasoning content is available in the response
    assert response.choices[0].message.reasoning_content == reasoning_content
    assert response.choices[0].message.content == content


def test_reasoning_content_only_on_first_action_with_multiple_tool_calls():
    """Test that reasoning content is only added to the first action when there are multiple tool calls."""
    reasoning_content = 'I need to run multiple commands to complete this task.'
    content = 'Let me run a few commands.'

    tool_calls = [
        {
            'function': {
                'name': 'execute_bash',
                'arguments': json.dumps({'command': 'ls -la'}),
            },
            'id': 'mock-tool-call-id-1',
            'type': 'function',
        },
        {
            'function': {
                'name': 'execute_bash',
                'arguments': json.dumps({'command': 'pwd'}),
            },
            'id': 'mock-tool-call-id-2',
            'type': 'function',
        },
    ]

    response = create_mock_response_with_reasoning(
        content=content, reasoning_content=reasoning_content, tool_calls=tool_calls
    )

    actions = response_to_actions(response)

    # Should have two actions
    assert len(actions) == 2

    # First action should have reasoning content
    assert hasattr(actions[0], 'reasoning_content')
    assert actions[0].reasoning_content == reasoning_content

    # Second action should not have reasoning content
    assert hasattr(actions[1], 'reasoning_content')
    assert actions[1].reasoning_content is None


def test_empty_reasoning_content():
    """Test behavior when reasoning content is None or empty."""
    response = create_mock_response_with_reasoning(
        content='Regular response', reasoning_content=None
    )

    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert actions[0].content == 'Regular response'
    assert actions[0].reasoning_content is None

    # Test with empty string
    response = create_mock_response_with_reasoning(
        content='Regular response', reasoning_content=''
    )

    actions = response_to_actions(response)
    assert len(actions) == 1
    assert isinstance(actions[0], MessageAction)
    assert actions[0].content == 'Regular response'
    assert actions[0].reasoning_content is None
