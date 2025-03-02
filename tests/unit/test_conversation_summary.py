"""Tests for the conversation summary generator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.utils.conversation_summary import generate_conversation_title


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
