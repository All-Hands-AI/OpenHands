"""Tests for the conversation stats API endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from openhands.llm.metrics import Metrics
from openhands.server.data_models.metrics_response import ConversationMetricsResponse
from openhands.server.routes.conversation import get_conversation_stats
from openhands.storage.memory import InMemoryFileStore


@pytest.mark.asyncio
async def test_get_conversation_stats_success():
    """Test successful retrieval of conversation stats."""
    # Create mock file store with metrics data
    mock_file_store = InMemoryFileStore({})

    # Create mock session manager
    mock_session_manager = MagicMock()
    mock_session_manager.file_store = mock_file_store
    mock_session_manager.sessions = {}

    # Create mock conversation store
    mock_conversation_store = MagicMock()
    mock_conversation_store.get_conversation_metadata = AsyncMock(return_value=None)

    # Create mock request
    mock_request = MagicMock()
    mock_request.app.state.session_manager = mock_session_manager
    mock_request.app.state.conversation_store = mock_conversation_store

    # Mock ConversationStats to return some test data
    with patch(
        'openhands.server.services.conversation_stats.ConversationStats'
    ) as mock_stats_class:
        mock_stats = MagicMock()
        mock_stats.restored_metrics = {}
        mock_stats.service_to_metrics = {}
        mock_stats_class.return_value = mock_stats

        # Call the endpoint
        result = await get_conversation_stats('test-conversation-id', mock_request)

        # Verify the result
        assert isinstance(result, ConversationMetricsResponse)
        assert result.conversation_id == 'test-conversation-id'
        assert result.metrics is None
        assert result.service_metrics == {}
        assert result.has_active_session is False


@pytest.mark.asyncio
async def test_get_conversation_stats_with_metrics():
    """Test retrieval of conversation stats with actual metrics data."""
    # Create mock file store
    mock_file_store = InMemoryFileStore({})

    # Create mock session manager
    mock_session_manager = MagicMock()
    mock_session_manager.file_store = mock_file_store
    mock_session_manager.sessions = {'test-conversation-id': MagicMock()}

    # Create mock conversation store
    mock_conversation_store = MagicMock()
    mock_conversation_store.get_conversation_metadata = AsyncMock(return_value=None)

    # Create mock request
    mock_request = MagicMock()
    mock_request.app.state.session_manager = mock_session_manager
    mock_request.app.state.conversation_store = mock_conversation_store

    # Create test metrics
    test_metrics = Metrics(model_name='gpt-4')
    test_metrics.add_cost(0.05)
    test_metrics.add_token_usage(
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=0,
        cache_write_tokens=0,
        context_window=8000,
        response_id='test-response',
    )

    # Mock ConversationStats to return test metrics
    with patch(
        'openhands.server.services.conversation_stats.ConversationStats'
    ) as mock_stats_class:
        mock_stats = MagicMock()
        mock_stats.restored_metrics = {}
        mock_stats.service_to_metrics = {'test-service': test_metrics}
        mock_stats.get_combined_metrics.return_value = test_metrics
        mock_stats_class.return_value = mock_stats

        # Call the endpoint
        result = await get_conversation_stats('test-conversation-id', mock_request)

        # Verify the result
        assert isinstance(result, ConversationMetricsResponse)
        assert result.conversation_id == 'test-conversation-id'
        assert result.metrics is not None
        assert result.metrics.accumulated_cost == 0.05
        assert result.service_metrics['test-service'].accumulated_cost == 0.05
        assert result.has_active_session is True


@pytest.mark.asyncio
async def test_get_conversation_stats_no_file_store():
    """Test error handling when file store is not available."""
    # Create mock request with no file store
    mock_request = MagicMock()
    mock_request.app.state.session_manager = None

    # Call the endpoint and expect an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_conversation_stats('test-conversation-id', mock_request)

    assert exc_info.value.status_code == 500
    assert 'File store not available' in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_conversation_stats_exception_handling():
    """Test error handling when an exception occurs."""
    # Create mock file store
    mock_file_store = InMemoryFileStore({})

    # Create mock session manager
    mock_session_manager = MagicMock()
    mock_session_manager.file_store = mock_file_store
    mock_session_manager.sessions = {}

    # Create mock conversation store
    mock_conversation_store = MagicMock()
    mock_conversation_store.get_conversation_metadata = AsyncMock(return_value=None)

    # Create mock request
    mock_request = MagicMock()
    mock_request.app.state.session_manager = mock_session_manager
    mock_request.app.state.conversation_store = mock_conversation_store

    # Mock ConversationStats to raise an exception
    with patch(
        'openhands.server.services.conversation_stats.ConversationStats'
    ) as mock_stats_class:
        mock_stats_class.side_effect = Exception('Test error')

        # Call the endpoint and expect an HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_conversation_stats('test-conversation-id', mock_request)

        assert exc_info.value.status_code == 500
        assert 'Error getting conversation stats: Test error' in str(
            exc_info.value.detail
        )
