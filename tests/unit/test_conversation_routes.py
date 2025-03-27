import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Request
from fastapi.responses import JSONResponse

from openhands.llm.metrics import Metrics, TokenUsage
from openhands.server.routes.conversation import get_conversation_metrics


@pytest.mark.asyncio
async def test_get_conversation_metrics():
    # Create mock request
    mock_request = MagicMock(spec=Request)

    # Create mock metrics
    mock_metrics = MagicMock(spec=Metrics)
    mock_metrics.model_name = 'test-model'
    mock_metrics.accumulated_cost = 0.25
    mock_metrics._accumulated_token_usage = TokenUsage(
        model='test-model',
        prompt_tokens=100,
        completion_tokens=50,
        cache_read_tokens=20,
        cache_write_tokens=10,
        response_id='test-response',
    )

    # Create mock LLM
    mock_llm = MagicMock()
    mock_llm.metrics = mock_metrics

    # Create mock agent
    mock_agent = MagicMock()
    mock_agent.llm = mock_llm

    # Create mock controller
    mock_controller = MagicMock()
    mock_controller.agent = mock_agent

    # Create mock agent_session
    mock_agent_session = MagicMock()
    mock_agent_session.controller = mock_controller

    # Create mock runtime
    mock_runtime = MagicMock()
    mock_runtime.agent_session = mock_agent_session

    # Create mock conversation
    mock_conversation = MagicMock()
    mock_conversation.runtime = mock_runtime

    # Set up request state
    mock_request.state.conversation = mock_conversation

    # Mock JSONResponse
    with patch('openhands.server.routes.conversation.JSONResponse') as mock_json_response:
        mock_json_response.return_value = JSONResponse(
            status_code=200,
            content={
                'model': 'test-model',
                'total_cost': 0.25,
                'total_input_tokens': 100,
                'total_output_tokens': 50,
                'total_cache_hit_tokens': 20,
            },
        )

        # Call the function
        result = await get_conversation_metrics(mock_request)

        # Verify JSONResponse was called with correct arguments
        mock_json_response.assert_called_once_with(
            status_code=200,
            content={
                'model': 'test-model',
                'total_cost': 0.25,
                'total_input_tokens': 100,
                'total_output_tokens': 50,
                'total_cache_hit_tokens': 20,
            },
        )