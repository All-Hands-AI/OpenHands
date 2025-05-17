"""Tests for the conversation summary generator."""

from unittest.mock import MagicMock, patch

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
    # Create a proper mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'Generated Title'

    # Create a mock LLM instance with a synchronous completion method
    mock_llm = MagicMock()
    mock_llm.completion = MagicMock(return_value=mock_response)

    # Patch the LLM class to return our mock
    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model')
        )

    assert result == 'Generated Title'
    # Verify the mock was called with the expected arguments
    mock_llm.completion.assert_called_once()


@pytest.mark.asyncio
async def test_generate_conversation_title_long_title():
    """Test that long titles are truncated."""
    # Create a proper mock response with a long title
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = 'This is a very long title that should be truncated because it exceeds the maximum length'

    # Create a mock LLM instance with a synchronous completion method
    mock_llm = MagicMock()
    mock_llm.completion = MagicMock(return_value=mock_response)

    # Patch the LLM class to return our mock
    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model'), max_length=30
        )

    # Verify the title is truncated correctly
    assert len(result) <= 30
    assert result.endswith('...')


@pytest.mark.asyncio
async def test_generate_conversation_title_exception():
    """Test that exceptions are handled gracefully."""
    # Create a mock LLM instance with a synchronous completion method that raises an exception
    mock_llm = MagicMock()
    mock_llm.completion = MagicMock(side_effect=Exception('Test error'))

    # Patch the LLM class to return our mock
    with patch('openhands.utils.conversation_summary.LLM', return_value=mock_llm):
        result = await generate_conversation_title(
            'Can you help me with Python?', LLMConfig(model='test-model')
        )

    # Verify that None is returned when an exception occurs
    assert result is None
