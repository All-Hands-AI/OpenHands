from openhands.core.config import LLMConfig
from openhands.core.message import Message, TextContent
from openhands.llm.llm import LLM


def test_get_token_count_with_stored_tokens():
    """Test get_token_count when messages have stored token counts."""
    config = LLMConfig(model='test-model')
    llm = LLM(config)

    # Create messages with stored token counts
    messages = [
        Message(
            role='user',
            content=[TextContent(text='Hello')],
            usage=type('Usage', (), {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5})(),
        ),
        Message(
            role='assistant',
            content=[TextContent(text='Hi there')],
            usage=type('Usage', (), {'prompt_tokens': 4, 'completion_tokens': 6, 'total_tokens': 10})(),
        ),
    ]

    # Should return sum of stored token counts
    assert llm.get_token_count(messages) == 15


def test_get_token_count_fallback():
    """Test get_token_count fallback to litellm when some messages don't have stored counts."""
    config = LLMConfig(model='test-model')
    llm = LLM(config)

    # Create messages with mixed token count availability
    messages = [
        Message(
            role='user',
            content=[TextContent(text='Hello')],
            usage=type('Usage', (), {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5})(),
        ),
        Message(
            role='assistant',
            content=[TextContent(text='Hi there')],
            # No usage set
        ),
    ]

    # Should fallback to litellm token counter
    # Since test-model is not supported, it will return 0
    assert llm.get_token_count(messages) == 0


def test_update_message_token_counts():
    """Test updating token counts in a message from usage data."""
    config = LLMConfig(model='test-model')
    llm = LLM(config)

    # Create a message and usage data
    message = Message(
        role='assistant',
        content=[TextContent(text='Hello')],
    )
    usage = type(
        'Usage',
        (),
        {
            'prompt_tokens': 5,
            'completion_tokens': 10,
            'total_tokens': 15,
        },
    )()

    # Update token counts
    llm._update_message_token_counts(message, usage)

    # Check that token counts were updated
    assert message.usage == usage  # Direct usage object comparison
    # Check that properties still work
    assert message.prompt_tokens == 5
    assert message.completion_tokens == 10
    assert message.total_tokens == 15


def test_get_token_count_with_event_id():
    """Test get_token_count with messages linked to events."""
    config = LLMConfig(model='test-model')
    llm = LLM(config)

    # Create messages with stored token counts and event_ids
    messages = [
        Message(
            role='user',
            content=[TextContent(text='Hello')],
            usage=type('Usage', (), {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 5})(),
            event_id=1,
        ),
        Message(
            role='assistant',
            content=[TextContent(text='Hi there')],
            usage=type('Usage', (), {'prompt_tokens': 4, 'completion_tokens': 6, 'total_tokens': 10})(),
            event_id=2,
        ),
    ]

    # Should return sum of stored token counts
    assert llm.get_token_count(messages) == 15
    assert messages[0].event_id == 1
    assert messages[1].event_id == 2
