"""Tests for the conversation summary generator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.utils.conversation_summary import (
    generate_conversation_title,
    update_conversation_title_if_needed,
)


@pytest.mark.asyncio
async def test_generate_conversation_title_empty_message():
    """Test that an empty message returns None."""
    result = await generate_conversation_title('', MagicMock())
    assert result is None

    result = await generate_conversation_title('   ', MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_generate_conversation_title_success():
    """Test successful title generation."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'Generated Title'

    # Set up the async mock correctly
    mock_llm.completion = AsyncMock(return_value=mock_response)

    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model')
        )

    assert result == 'Generated Title'
    mock_llm.completion.assert_called_once()


@pytest.mark.asyncio
async def test_generate_conversation_title_long_title():
    """Test that long titles are truncated."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = 'This is a very long title that should be truncated because it exceeds the maximum length'

    # Set up the async mock correctly
    mock_llm.completion = AsyncMock(return_value=mock_response)

    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model'), max_length=30
        )

    assert len(result) <= 30
    assert result.endswith('...')


@pytest.mark.asyncio
async def test_generate_conversation_title_exception():
    """Test that exceptions are handled gracefully."""
    mock_llm = MagicMock()
    mock_llm.completion = AsyncMock(side_effect=Exception('Test error'))

    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model')
        )

    assert result is None


@pytest.mark.asyncio
async def test_update_conversation_title_if_needed_no_default_title():
    """Test that a conversation with a non-default title is not updated."""
    # Setup
    conversation_id = '12345abcde'
    mock_metadata = MagicMock()
    mock_metadata.title = 'Custom Title'  # Not a default title

    mock_conversation_store = MagicMock()
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)

    # Execute
    result = await update_conversation_title_if_needed(
        conversation_id, mock_conversation_store, MagicMock(), MagicMock()
    )

    # Assert
    assert result is False
    mock_conversation_store.get_metadata.assert_called_once_with(conversation_id)
    mock_conversation_store.save_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_update_conversation_title_if_needed_default_title_no_message():
    """Test that a conversation with a default title but no user message is not updated."""
    # Setup
    conversation_id = '12345abcde'
    mock_metadata = MagicMock()
    mock_metadata.title = f'Conversation {conversation_id[:5]}'  # Default title

    mock_conversation_store = MagicMock()
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)

    mock_event_stream = MagicMock()
    mock_event_stream.get_events = MagicMock(return_value=[])  # No events

    # Execute
    result = await update_conversation_title_if_needed(
        conversation_id, mock_conversation_store, mock_event_stream, MagicMock()
    )

    # Assert
    assert result is False
    mock_conversation_store.get_metadata.assert_called_once_with(conversation_id)
    mock_conversation_store.save_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_update_conversation_title_if_needed_success():
    """Test successful title update for a conversation with a default title and user message."""
    # Setup
    conversation_id = '12345abcde'
    mock_metadata = MagicMock()
    mock_metadata.title = f'Conversation {conversation_id[:5]}'  # Default title

    mock_conversation_store = MagicMock()
    mock_conversation_store.get_metadata = AsyncMock(return_value=mock_metadata)
    mock_conversation_store.save_metadata = AsyncMock()

    # Create a mock message action
    mock_message = MagicMock(spec=MessageAction)
    mock_message.content = 'Can you help me with Python?'
    mock_message.source = EventSource.USER

    mock_event_stream = MagicMock()
    mock_event_stream.get_events = MagicMock(return_value=[mock_message])

    # Mock the generate_conversation_title function
    with patch(
        'openhands.utils.conversation_summary.generate_conversation_title',
        new=AsyncMock(return_value='Python Help Request'),
    ):
        # Execute
        result = await update_conversation_title_if_needed(
            conversation_id,
            mock_conversation_store,
            mock_event_stream,
            LLMConfig(model='test-model'),
        )

    # Assert
    assert result is True
    mock_conversation_store.get_metadata.assert_called_once_with(conversation_id)
    mock_conversation_store.save_metadata.assert_called_once()
    assert mock_metadata.title == 'Python Help Request'
