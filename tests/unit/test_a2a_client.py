from unittest.mock import AsyncMock, Mock, patch
import pytest
from openhands.runtime.plugins.agent_skills.a2a_client.a2a_client import send_task_A2A, completeTask
from openhands.runtime.plugins.agent_skills.a2a_client.common.types import TaskState

@pytest.mark.asyncio
@patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2ACardResolver")
@patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient")
async def test_send_task_A2A(mock_a2a_client, mock_card_resolver):
    # Mock card resolver and agent card
    mock_card = Mock()
    mock_card.capabilities.streaming = False
    mock_card.model_dump_json.return_value = "{}"
    mock_card_resolver.return_value.get_agent_card.return_value = mock_card

    # Mock A2AClient
    mock_client = Mock()
    mock_a2a_client.return_value = mock_client

    # Mock completeTask
    with patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.completeTask", new=AsyncMock()) as mock_complete_task:
        await send_task_A2A("http://example.com", "test message")

        # Assert card resolver and client initialization
        mock_card_resolver.assert_called_once_with("http://example.com")
        mock_card_resolver.return_value.get_agent_card.assert_called_once()
        mock_a2a_client.assert_called_once_with(agent_card=mock_card)

        # Assert completeTask is called with correct arguments
        mock_complete_task.assert_called_once()
        _, _, streaming, task_id, session_id = mock_complete_task.call_args[0]
        assert streaming is False
        assert len(task_id) > 0
        assert len(session_id) > 0


@pytest.mark.asyncio
@patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient")
async def test_completeTask_non_streaming(mock_a2a_client):
    # Mock A2AClient
    mock_client = Mock()
    mock_client.send_task = AsyncMock(return_value=Mock(result=Mock(status=Mock(state=TaskState.COMPLETED.value))))
    mock_a2a_client.return_value = mock_client

    # Call completeTask
    result = await completeTask(mock_client, "test message", False, "task_id", "session_id")

    # Assert payload construction
    mock_client.send_task.assert_called_once()
    payload = mock_client.send_task.call_args[0][0]
    assert payload["id"] == "task_id"
    assert payload["sessionId"] == "session_id"
    assert payload["message"]["role"] == "user"
    assert payload["message"]["parts"][0]["text"] == "test message"

    # Assert task completion
    assert result is True


@pytest.mark.asyncio
@patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient")
async def test_completeTask_streaming(mock_a2a_client):
    # Mock A2AClient
    mock_client = Mock()
    mock_client.send_task_streaming = Mock(return_value=AsyncMock())
    mock_client.get_task = AsyncMock(return_value=Mock(result=Mock(status=Mock(state=TaskState.COMPLETED.value))))
    mock_a2a_client.return_value = mock_client

    # Call completeTask
    result = await completeTask(mock_client, "test message", True, "task_id", "session_id")

    # Assert streaming task handling
    mock_client.send_task_streaming.assert_called_once()
    mock_client.get_task.assert_called_once_with({"id": "task_id"})

    # Assert task completion
    assert result is True


@pytest.mark.asyncio
@patch("openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient")
async def test_completeTask_input_required(mock_a2a_client):
    # Mock A2AClient
    mock_client = Mock()
    mock_client.send_task = AsyncMock(return_value=Mock(result=Mock(status=Mock(state=TaskState.INPUT_REQUIRED.value))))
    mock_a2a_client.return_value = mock_client

    # Call completeTask
    result = await completeTask(mock_client, "test message", False, "task_id", "session_id")

    # Assert task requires more input
    assert result is None