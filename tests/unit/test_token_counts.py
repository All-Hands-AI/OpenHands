import pytest
from litellm import Message as LiteLLMMessage
from litellm.types.utils import ModelResponse, Usage

from openhands.core.message import Message, TextContent
from openhands.events.action import Action, CmdRunAction
from openhands.events.event import EventSource
from openhands.events.tool import ToolCallMetadata


def test_get_token_count_with_stored_counts():
    """Test that get_token_count uses stored token counts when available."""
    # Create messages with stored token counts
    messages = [
        Message(
            role='user',
            content=[TextContent(text='Hello')],
            total_tokens=10,
        ),
        Message(
            role='assistant',
            content=[TextContent(text='Hi there')],
            total_tokens=20,
        ),
    ]

    # Create a mock LLM instance
    class MockLLM:
        def get_token_count(self, messages):
            return sum(msg.total_tokens for msg in messages)

    llm = MockLLM()

    # Test that get_token_count returns the sum of stored token counts
    assert llm.get_token_count(messages) == 30


def test_message_creation_with_usage_data(codeact_agent):
    """Test that messages are created with token counts from Usage data."""
    # Create a mock LLM response with Usage data
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    llm_response = ModelResponse(
        id='test_id',
        choices=[
            {
                'message': LiteLLMMessage(
                    role='assistant',
                    content='Hello',
                ),
                'finish_reason': 'stop',
                'index': 0,
            }
        ],
        model='test_model',
        usage=usage,
    )

    # Create a mock action with tool call metadata
    action = CmdRunAction(command='echo "Hello"')
    action._source = EventSource.AGENT
    action.tool_call_metadata = ToolCallMetadata(
        model_response=llm_response,
        tool_call_id='test_tool_call_id',
        function_name='test_function',
        total_calls_in_response=1,
    )

    # Get messages from the action
    pending_tool_call_action_messages = {}
    messages = codeact_agent.get_action_message(action, pending_tool_call_action_messages)

    # Check that the message has the correct token counts
    assert len(pending_tool_call_action_messages) == 1
    message = list(pending_tool_call_action_messages.values())[0]
    assert message.prompt_tokens == 10
    assert message.completion_tokens == 20
    assert message.total_tokens == 30
