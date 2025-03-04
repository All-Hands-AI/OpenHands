from unittest.mock import MagicMock

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from openhands.llm.metrics import Metrics, TokenUsage
from openhands.server.routes.conversation import get_conversation_metrics


@pytest.fixture
def mock_request():
    """Create a mock request with a conversation."""
    request = MagicMock(spec=Request)
    request.state.conversation = MagicMock()
    request.state.conversation.runtime = MagicMock()
    request.state.conversation.event_stream = MagicMock()
    # Add get_metrics method to conversation mock
    request.state.conversation.get_metrics = MagicMock()
    return request


@pytest.mark.asyncio
async def test_get_conversation_metrics_success(mock_request):
    """Test successful retrieval of conversation metrics from runtime state."""
    # Setup mock metrics
    metrics = Metrics()
    metrics.token_usages = [
        TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            model='test-model',
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id='test-response-1',
        ),
        TokenUsage(
            prompt_tokens=200,
            completion_tokens=150,
            model='test-model',
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id='test-response-2',
        ),
    ]
    metrics.accumulated_cost = 0.25

    # Configure mock to return metrics from runtime state
    mock_request.state.conversation.get_metrics.return_value = metrics

    # Call the endpoint
    response = await get_conversation_metrics(mock_request)

    # Verify response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_200_OK

    # Extract content from JSONResponse
    content = response.body.decode('utf-8')
    import json

    content_dict = json.loads(content)

    # Verify metrics
    assert content_dict['accumulated_cost'] == 0.25
    assert content_dict['total_prompt_tokens'] == 300
    assert content_dict['total_completion_tokens'] == 200
    assert content_dict['total_tokens'] == 500

    # Verify get_metrics was called on the conversation
    mock_request.state.conversation.get_metrics.assert_called_once()
    # Verify event_stream.get_metrics was not called
    mock_request.state.conversation.event_stream.get_metrics.assert_not_called()


@pytest.mark.asyncio
async def test_get_conversation_metrics_fallback_to_event_stream(mock_request):
    """Test fallback to event_stream metrics when runtime state metrics are not available."""
    # Setup mock metrics
    metrics = Metrics()
    metrics.token_usages = [
        TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            model='test-model',
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id='test-response-1',
        ),
    ]
    metrics.accumulated_cost = 0.15

    # Configure mock to return None from runtime state but metrics from event_stream
    mock_request.state.conversation.get_metrics.return_value = None
    mock_request.state.conversation.event_stream.get_metrics.return_value = metrics

    # Call the endpoint
    response = await get_conversation_metrics(mock_request)

    # Verify response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_200_OK

    # Extract content from JSONResponse
    content = response.body.decode('utf-8')
    import json

    content_dict = json.loads(content)

    # Verify metrics from event_stream were used
    assert content_dict['accumulated_cost'] == 0.15
    assert content_dict['total_prompt_tokens'] == 100
    assert content_dict['total_completion_tokens'] == 50
    assert content_dict['total_tokens'] == 150

    # Verify both methods were called
    mock_request.state.conversation.get_metrics.assert_called_once()
    mock_request.state.conversation.event_stream.get_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_metrics_no_metrics(mock_request):
    """Test handling when no metrics are available from either source."""
    # Configure mocks to return None for metrics
    mock_request.state.conversation.get_metrics.return_value = None
    mock_request.state.conversation.event_stream.get_metrics.return_value = None

    # Call the endpoint
    response = await get_conversation_metrics(mock_request)

    # Verify response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_200_OK

    # Extract content from JSONResponse
    content = response.body.decode('utf-8')
    import json

    content_dict = json.loads(content)

    # Verify default metrics
    assert content_dict['accumulated_cost'] == 0.0
    assert content_dict['total_prompt_tokens'] == 0
    assert content_dict['total_completion_tokens'] == 0
    assert content_dict['total_tokens'] == 0

    # Verify both methods were called
    mock_request.state.conversation.get_metrics.assert_called_once()
    mock_request.state.conversation.event_stream.get_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_metrics_no_conversation():
    """Test handling when no conversation is found in request state."""
    # Create a request without conversation
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Remove conversation attribute
    delattr(request.state, 'conversation')

    # Call the endpoint
    response = await get_conversation_metrics(request)

    # Verify response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Extract content from JSONResponse
    content = response.body.decode('utf-8')
    import json

    content_dict = json.loads(content)

    # Verify error message
    assert 'error' in content_dict
    assert 'No conversation found in request state' in content_dict['error']


@pytest.mark.asyncio
async def test_get_conversation_metrics_exception(mock_request):
    """Test handling when an exception occurs."""
    # Configure mock to raise an exception
    mock_request.state.conversation.get_metrics.side_effect = Exception(
        'Test exception'
    )

    # Call the endpoint
    response = await get_conversation_metrics(mock_request)

    # Verify response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Extract content from JSONResponse
    content = response.body.decode('utf-8')
    import json

    content_dict = json.loads(content)

    # Verify error message
    assert 'error' in content_dict
    assert 'Error getting conversation metrics' in content_dict['error']
