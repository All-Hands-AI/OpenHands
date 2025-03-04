import pytest
from unittest.mock import MagicMock, patch

from fastapi import Request, status
from fastapi.responses import JSONResponse
from openhands.llm.metrics import Metrics, TokenUsage
from openhands.server.routes.conversation import get_conversation_metrics


@pytest.fixture
def mock_metrics():
    metrics = Metrics()
    metrics.accumulated_cost = 0.25
    metrics.token_usages = [
        TokenUsage(
            model="gpt-4", 
            prompt_tokens=100, 
            completion_tokens=50, 
            cache_read_tokens=0, 
            cache_write_tokens=0, 
            response_id="resp1"
        ),
        TokenUsage(
            model="gpt-4", 
            prompt_tokens=200, 
            completion_tokens=75, 
            cache_read_tokens=0, 
            cache_write_tokens=0, 
            response_id="resp2"
        ),
    ]
    return metrics


@pytest.mark.asyncio
async def test_get_conversation_metrics_success(mock_metrics):
    """Test that the metrics endpoint returns the correct metrics data."""
    
    # Create a mock request with a conversation that has metrics
    mock_event_stream = MagicMock()
    mock_event_stream.get_metrics.return_value = mock_metrics
    
    mock_conversation = MagicMock()
    mock_conversation.event_stream = mock_event_stream
    
    mock_request = MagicMock()
    mock_request.state.conversation = mock_conversation
    
    # Call the endpoint function directly
    response = await get_conversation_metrics(mock_request)
    
    # Check the response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_200_OK
    
    # Extract the content from the response
    content = response.body.decode('utf-8')
    import json
    data = json.loads(content)
    
    # Verify the metrics data
    assert data["accumulated_cost"] == 0.25
    assert data["total_prompt_tokens"] == 300
    assert data["total_completion_tokens"] == 125
    assert data["total_tokens"] == 425
    
    # Verify the get_metrics method was called
    mock_conversation.event_stream.get_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_metrics_no_metrics():
    """Test that the metrics endpoint handles the case where no metrics are available."""
    
    # Create a mock request with a conversation that has no metrics
    mock_event_stream = MagicMock()
    mock_event_stream.get_metrics.return_value = None
    
    mock_conversation = MagicMock()
    mock_conversation.event_stream = mock_event_stream
    
    mock_request = MagicMock()
    mock_request.state.conversation = mock_conversation
    
    # Call the endpoint function directly
    response = await get_conversation_metrics(mock_request)
    
    # Check the response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_200_OK
    
    # Extract the content from the response
    content = response.body.decode('utf-8')
    import json
    data = json.loads(content)
    
    # Verify the metrics data
    assert data["accumulated_cost"] == 0.0
    assert data["total_prompt_tokens"] == 0
    assert data["total_completion_tokens"] == 0
    assert data["total_tokens"] == 0
    
    # Verify the get_metrics method was called
    mock_conversation.event_stream.get_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_metrics_no_conversation():
    """Test that the metrics endpoint handles the case where no conversation is found."""
    
    # Create a mock request with no conversation attribute
    mock_request = MagicMock()
    mock_request.state = MagicMock()
    # Intentionally not setting request.state.conversation
    
    # Call the endpoint function directly
    response = await get_conversation_metrics(mock_request)
    
    # Check the response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Extract the content from the response
    content = response.body.decode('utf-8')
    import json
    data = json.loads(content)
    
    # Verify the error message
    assert "error" in data
    assert "No conversation found" in data["error"] or "conversation" in data["error"].lower()


@pytest.mark.asyncio
async def test_get_conversation_metrics_exception():
    """Test that the metrics endpoint handles exceptions gracefully."""
    
    # Create a mock request with a conversation that raises an exception
    mock_event_stream = MagicMock()
    mock_event_stream.get_metrics.side_effect = Exception("Test exception")
    
    mock_conversation = MagicMock()
    mock_conversation.event_stream = mock_event_stream
    
    mock_request = MagicMock()
    mock_request.state.conversation = mock_conversation
    
    # Call the endpoint function directly
    response = await get_conversation_metrics(mock_request)
    
    # Check the response
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Extract the content from the response
    content = response.body.decode('utf-8')
    import json
    data = json.loads(content)
    
    # Verify the error message
    assert "error" in data
    assert "Test exception" in data["error"]
    
    # Verify the get_metrics method was called
    mock_conversation.event_stream.get_metrics.assert_called_once()