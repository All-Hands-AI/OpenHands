import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from httpx import HTTPStatusError, Request, Response
from httpx_sse import ServerSentEvent

from openhands.runtime.plugins.agent_skills.a2a_client.a2a_client import (
    completeTask,
    send_task_A2A,
)
from openhands.runtime.plugins.agent_skills.a2a_client.common.client import (
    A2ACardResolver,
    A2AClient,
)
from openhands.runtime.plugins.agent_skills.a2a_client.common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    JSONRPCRequest,
    SendTaskRequest,
    SendTaskResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

# Tests for openhands/runtime/plugins/agent_skills/a2a_client/a2a_client.py


@pytest.mark.asyncio
@patch('openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2ACardResolver')
@patch('openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient')
async def test_send_task_A2A(mock_a2a_client, mock_card_resolver):
    # Mock: card resolver, agent card, A2A Client and completeTask
    mock_card = Mock()
    mock_card.capabilities.streaming = False
    mock_card.model_dump_json.return_value = '{}'
    mock_card_resolver.return_value.get_agent_card.return_value = mock_card

    mock_client = Mock()
    mock_a2a_client.return_value = mock_client

    with patch(
        'openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.completeTask',
        new=AsyncMock(),
    ) as mock_complete_task:
        await send_task_A2A('http://example.com', 'test message')

        mock_card_resolver.assert_called_once_with('http://example.com')
        mock_card_resolver.return_value.get_agent_card.assert_called_once()
        mock_a2a_client.assert_called_once_with(agent_card=mock_card)

        mock_complete_task.assert_called_once()
        _, _, streaming, task_id, session_id = mock_complete_task.call_args[0]
        assert streaming is False
        assert len(task_id) > 0
        assert len(session_id) > 0


@pytest.mark.asyncio
@patch('openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient')
async def test_completeTask_non_streaming(mock_a2a_client):
    # Mock: A2AClient
    mock_client = Mock()
    mock_client.send_task = AsyncMock(
        return_value=Mock(result=Mock(status=Mock(state=TaskState.COMPLETED.value)))
    )
    mock_a2a_client.return_value = mock_client

    result = await completeTask(
        mock_client, 'test message', False, 'task_id', 'session_id'
    )

    mock_client.send_task.assert_called_once()
    payload = mock_client.send_task.call_args[0][0]
    assert payload['id'] == 'task_id'
    assert payload['sessionId'] == 'session_id'
    assert payload['message']['role'] == 'user'
    assert payload['message']['parts'][0]['text'] == 'test message'
    assert result is True


@pytest.mark.asyncio
@patch('openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient')
async def test_completeTask_streaming(mock_a2a_client):
    # Mock A2AClient
    mock_client = Mock()
    mock_client.send_task_streaming = Mock(return_value=AsyncMock())
    mock_client.get_task = AsyncMock(
        return_value=Mock(result=Mock(status=Mock(state=TaskState.COMPLETED.value)))
    )
    mock_a2a_client.return_value = mock_client

    result = await completeTask(
        mock_client, 'test message', True, 'task_id', 'session_id'
    )

    mock_client.send_task_streaming.assert_called_once()
    mock_client.get_task.assert_called_once_with({'id': 'task_id'})
    assert result is True


@pytest.mark.asyncio
@patch('openhands.runtime.plugins.agent_skills.a2a_client.a2a_client.A2AClient')
async def test_completeTask_input_required(mock_a2a_client):
    # Mock A2AClient
    mock_client = Mock()
    mock_client.send_task = AsyncMock(
        return_value=Mock(
            result=Mock(status=Mock(state=TaskState.INPUT_REQUIRED.value))
        )
    )
    mock_a2a_client.return_value = mock_client

    result = await completeTask(
        mock_client, 'test message', False, 'task_id', 'session_id'
    )

    assert result is None


# Tests for openhands/runtime/plugins/agent_skills/a2a_client/common/client/client.py
TEST_URL = 'https://example.com'


def make_mock_request() -> JSONRPCRequest:
    return JSONRPCRequest(
        jsonrpc='2.0',
        id='1',
        method='test_method',
        params={},
    )


@pytest.mark.asyncio
async def test__send_request_success():
    mock_request = make_mock_request()
    mock_response_data = {
        'jsonrpc': '2.0',
        'id': '1',
        'method': 'test_method',
        'result': {},
    }

    client = A2AClient(url=TEST_URL)

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.return_value = mock_response_data

    mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', mock_post):
        result = await client._send_request(mock_request)

    assert result == mock_response_data
    mock_post.assert_awaited_once_with(
        TEST_URL, json=mock_request.model_dump(), timeout=30
    )


@pytest.mark.asyncio
async def test__send_request_http_error():
    mock_request = make_mock_request()
    client = A2AClient(url=TEST_URL)

    bad_request_response = Response(status_code=400, request=Request('POST', TEST_URL))

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        message='Bad Request',
        request=bad_request_response.request,
        response=bad_request_response,
    )
    mock_response.json.return_value = {}

    mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', mock_post):
        with pytest.raises(A2AClientHTTPError) as exc_info:
            await client._send_request(mock_request)

    assert exc_info.value.status_code == 400
    assert 'Bad Request' in str(exc_info.value)


@pytest.mark.asyncio
async def test__send_request_json_error():
    mock_request = make_mock_request()
    client = A2AClient(url=TEST_URL)

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json.side_effect = json.JSONDecodeError(
        msg='Expecting value', doc='', pos=0
    )

    mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', mock_post):
        with pytest.raises(A2AClientJSONError) as exc_info:
            await client._send_request(mock_request)

    assert 'Expecting value' in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_task():
    mock_payload = {
        'id': 'test-task-id',
        'sessionId': 'test-session-id',
        'message': {
            'role': 'user',
            'parts': [
                {
                    'type': 'text',
                    'text': 'Hello, world!',
                }
            ],
        },
    }
    mock_response_data = {
        'jsonrpc': '2.0',
        'id': '1',
        'result': {
            'id': 'test-task-id',
            'sessionId': 'test-session-id',
            'status': {
                'state': 'submitted',
                'timestamp': '2025-01-01T00:00:00Z',
            },
        },
    }

    client = A2AClient(url=TEST_URL)

    with patch.object(
        client, '_send_request', AsyncMock(return_value=mock_response_data)
    ) as mock_send:
        result = await client.send_task(mock_payload)

    assert isinstance(result, SendTaskResponse)
    assert result == SendTaskResponse(**mock_response_data)
    mock_send.assert_awaited_once()
    sent_arg = mock_send.call_args.args[0]
    assert isinstance(sent_arg, SendTaskRequest)
    assert sent_arg.params == TaskSendParams(**mock_payload)


@pytest.mark.asyncio
async def test_cancel_task():
    mock_payload = {'id': 'test-task-id'}
    mock_response_data = {
        'jsonrpc': '2.0',
        'id': '1',
        'result': {
            'id': 'test-task-id',
            'status': {
                'state': 'canceled',
                'timestamp': '2025-01-01T00:00:00Z',
            },
        },
    }

    client = A2AClient(url=TEST_URL)

    with patch.object(
        client, '_send_request', AsyncMock(return_value=mock_response_data)
    ) as mock_send:
        result = await client.cancel_task(mock_payload)

    assert isinstance(result, CancelTaskResponse)
    assert result == CancelTaskResponse(**mock_response_data)
    mock_send.assert_awaited_once()
    sent_arg = mock_send.call_args.args[0]
    assert isinstance(sent_arg, CancelTaskRequest)
    assert sent_arg.params == TaskIdParams(**mock_payload)


@pytest.mark.asyncio
async def test_set_task_callback():
    mock_payload = {
        'id': 'test-task-id',
        'pushNotificationConfig': {'url': 'https://callback.example.com'},
    }
    mock_response_data = {
        'jsonrpc': '2.0',
        'id': '1',
        'result': {
            'id': 'test-task-id',
            'pushNotificationConfig': {
                'url': 'https://callback.example.com',
            },
        },
    }

    client = A2AClient(url=TEST_URL)

    with patch.object(
        client, '_send_request', AsyncMock(return_value=mock_response_data)
    ) as mock_send:
        result = await client.set_task_callback(mock_payload)

    assert isinstance(result, SetTaskPushNotificationResponse)
    assert result == SetTaskPushNotificationResponse(**mock_response_data)
    mock_send.assert_awaited_once()
    sent_arg = mock_send.call_args.args[0]
    assert isinstance(sent_arg, SetTaskPushNotificationRequest)
    assert sent_arg.params == TaskPushNotificationConfig(**mock_payload)


@pytest.mark.asyncio
async def test_get_task_callback():
    mock_payload = {'id': 'test-task-id'}
    mock_response_data = {
        'jsonrpc': '2.0',
        'id': '1',
        'result': {
            'id': 'test-task-id',
            'pushNotificationConfig': {
                'url': 'https://callback.example.com',
            },
        },
    }

    client = A2AClient(url=TEST_URL)

    with patch.object(
        client, '_send_request', AsyncMock(return_value=mock_response_data)
    ) as mock_send:
        result = await client.get_task_callback(mock_payload)

    assert isinstance(result, GetTaskPushNotificationResponse)
    assert result == GetTaskPushNotificationResponse(**mock_response_data)
    mock_send.assert_awaited_once()
    sent_arg = mock_send.call_args.args[0]
    assert isinstance(sent_arg, GetTaskPushNotificationRequest)
    assert sent_arg.params == TaskIdParams(**mock_payload)


@pytest.mark.asyncio
async def test_send_task_streaming():
    mock_event_source = MagicMock()
    mock_event_source.iter_sse.return_value = iter(
        [
            ServerSentEvent(
                data=json.dumps(
                    {
                        'jsonrpc': '2.0',
                        'id': '1',
                        'result': {
                            'id': 'test-task-id',
                            'status': {
                                'state': 'submitted',
                                'timestamp': '2025-01-01T00:00:00Z',
                            },
                        },
                    }
                )
            ),
            ServerSentEvent(
                data=json.dumps(
                    {
                        'jsonrpc': '2.0',
                        'id': '1',
                        'result': {
                            'id': 'test-task-id',
                            'status': {
                                'state': 'working',
                                'timestamp': '2025-01-01T00:01:00Z',
                            },
                        },
                    }
                )
            ),
        ]
    )

    with patch(
        'openhands.runtime.plugins.agent_skills.a2a_client.common.client.client.connect_sse'
    ) as mock_connect_sse:
        mock_connect_sse.return_value.__enter__.return_value = mock_event_source

        client = A2AClient(url='http://mock.url')
        payload = {
            'id': 'test-task-id',
            'message': {'role': 'user', 'parts': [{'type': 'text', 'text': 'Hi'}]},
        }

        responses = []
        async for res in client.send_task_streaming(payload):
            responses.append(res)

        assert responses[0].result == TaskStatusUpdateEvent(
            id='test-task-id',
            status=TaskStatus(
                state='submitted',
                timestamp='2025-01-01T00:00:00Z',
            ),
            final=False,
        )

        assert responses[1].result == TaskStatusUpdateEvent(
            id='test-task-id',
            status=TaskStatus(
                state='working',
                timestamp='2025-01-01T00:01:00Z',
            ),
            final=False,
        )


# Tests for openhands/runtime/plugins/agent_skills/a2a_client/common/card_resolver.py


def test_get_agent_card_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'name': 'TestAgent',
        'version': '1.0',
        'capabilities': {
            'streaming': True,
        },
        'url': 'http://example.com',
        'skills': [
            {
                'id': 'test_skill_id',
                'name': 'test_skill_name',
            }
        ],
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        'openhands.runtime.plugins.agent_skills.a2a_client.common.client.client.httpx.Client'
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.get.return_value = mock_response

        resolver = A2ACardResolver('http://example.com')
        result = resolver.get_agent_card()

        assert isinstance(result, AgentCard)
        assert result.name == 'TestAgent'
        assert result.version == '1.0'


def test_get_agent_card_json_error():
    mock_response = MagicMock()
    mock_response.json.side_effect = json.JSONDecodeError('msg', 'doc', 0)
    mock_response.raise_for_status.return_value = None

    with patch(
        'openhands.runtime.plugins.agent_skills.a2a_client.common.client.client.httpx.Client'
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.get.return_value = mock_response

        resolver = A2ACardResolver('http://example.com')
        with pytest.raises(A2AClientJSONError):
            resolver.get_agent_card()
