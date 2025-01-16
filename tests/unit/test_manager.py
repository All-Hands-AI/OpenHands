import asyncio
import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from openhands.core.config.app_config import AppConfig
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.session.manager import SessionManager
from openhands.storage.memory import InMemoryFileStore


@dataclass
class GetMessageMock:
    message: dict | None
    sleep_time: int = 0.01

    async def get_message(self, **kwargs):
        await asyncio.sleep(self.sleep_time)
        return {'data': json.dumps(self.message)}


def get_mock_sio(get_message: GetMessageMock | None = None):
    sio = MagicMock()
    sio.enter_room = AsyncMock()
    sio.manager.redis = MagicMock()
    sio.manager.redis.publish = AsyncMock()
    pubsub = AsyncMock()
    pubsub.get_message = (get_message or GetMessageMock(None)).get_message
    sio.manager.redis.pubsub.return_value = pubsub
    return sio


@pytest.mark.asyncio
async def test_session_not_running_in_cluster():
    sio = get_mock_sio()
    id = uuid4()
    with (
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch('openhands.server.session.manager.uuid4', MagicMock(return_value=id)),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            result = await session_manager._get_running_agent_loops_remotely(
                filter_to_sids={'non-existant-session'}
            )
            assert result == set()
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'session_msg',
                '{"query_id": "'
                + str(id)
                + '", "message_type": "running_agent_loops_query", "filter_to_sids": ["non-existant-session"]}',
            )


@pytest.mark.asyncio
async def test_get_running_agent_loops_remotely():
    id = uuid4()
    sio = get_mock_sio(
        GetMessageMock(
            {
                'query_id': str(id),
                'sids': ['existing-session'],
                'message_type': 'running_agent_loops_response',
            }
        )
    )
    with (
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.1),
        patch('openhands.server.session.manager.uuid4', MagicMock(return_value=id)),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            result = await session_manager._get_running_agent_loops_remotely(
                1, {'existing-session'}
            )
            assert result == {'existing-session'}
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'session_msg',
                '{"query_id": "'
                + str(id)
                + '", "message_type": "running_agent_loops_query", "user_id": 1, "filter_to_sids": ["existing-session"]}',
            )


@pytest.mark.asyncio
async def test_init_new_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.1),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), 1
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData(), 1
            )
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 1


@pytest.mark.asyncio
async def test_join_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), None
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData(), None
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData(), None
            )
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 2


@pytest.mark.asyncio
async def test_join_cluster_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = {'new-session-id'}
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._get_running_agent_loops_remotely',
            get_running_agent_loops_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData(), 1
            )
    assert session_instance.initialize_agent.call_count == 0
    assert sio.enter_room.await_count == 1


@pytest.mark.asyncio
async def test_add_to_local_event_stream():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), 1
            )
            await session_manager.join_conversation(
                'new-session-id', 'connection-id', ConversationInitData(), 1
            )
            await session_manager.send_to_event_stream(
                'connection-id', {'event_type': 'some_event'}
            )
    session_instance.dispatch.assert_called_once_with({'event_type': 'some_event'})


@pytest.mark.asyncio
async def test_add_to_cluster_event_stream():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = {'new-session-id'}
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._get_running_agent_loops_remotely',
            get_running_agent_loops_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation(
                'new-session-id', 'connection-id', ConversationInitData(), 1
            )
            await session_manager.send_to_event_stream(
                'connection-id', {'event_type': 'some_event'}
            )
    assert sio.manager.redis.publish.await_count == 1
    sio.manager.redis.publish.assert_called_once_with(
        'session_msg',
        '{"sid": "new-session-id", "message_type": "event", "data": {"event_type": "some_event"}}',
    )


@pytest.mark.asyncio
async def test_cleanup_session_connections():
    sio = get_mock_sio()
    with (
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            session_manager._local_connection_id_to_session_id.update(
                {
                    'conn1': 'session1',
                    'conn2': 'session1',
                    'conn3': 'session2',
                    'conn4': 'session2',
                }
            )

            await session_manager._close_session('session1')

            remaining_connections = session_manager._local_connection_id_to_session_id
            assert 'conn1' not in remaining_connections
            assert 'conn2' not in remaining_connections
            assert 'conn3' in remaining_connections
            assert 'conn4' in remaining_connections
            assert remaining_connections['conn3'] == 'session2'
            assert remaining_connections['conn4'] == 'session2'
