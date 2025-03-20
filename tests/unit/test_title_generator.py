"""Tests for the title generator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.server.utils.title_generator import generate_conversation_title


@pytest.mark.asyncio
async def test_generate_conversation_title():
    """Test that the title generator returns a title."""
    # Create a mock LLM
    mock_llm = AsyncMock()
    mock_llm.acompletion.return_value = "Generated Title"
    
    # Call the function
    title = await generate_conversation_title("Test message", mock_llm)
    
    # Check that the LLM was called with the expected prompt
    mock_llm.acompletion.assert_called_once()
    prompt = mock_llm.acompletion.call_args[0][0]
    assert "Test message" in prompt
    assert "Generate a concise title" in prompt
    
    # Check that the title was returned
    assert title == "Generated Title"


@pytest.mark.asyncio
async def test_generate_conversation_title_long_response():
    """Test that the title generator truncates long titles."""
    # Create a mock LLM
    mock_llm = AsyncMock()
    mock_llm.acompletion.return_value = "A" * 100  # Very long title
    
    # Call the function
    title = await generate_conversation_title("Test message", mock_llm)
    
    # Check that the title was truncated
    assert len(title) <= 50
    assert title.endswith("...")


@pytest.mark.asyncio
async def test_generate_conversation_title_error():
    """Test that the title generator handles errors."""
    # Create a mock LLM that raises an exception
    mock_llm = AsyncMock()
    mock_llm.acompletion.side_effect = Exception("Test error")
    
    # Call the function
    title = await generate_conversation_title("Test message", mock_llm)
    
    # Check that a default title was returned
    assert title == "New Conversation"