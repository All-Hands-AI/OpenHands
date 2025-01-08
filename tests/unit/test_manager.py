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
            result = await session_manager.is_agent_loop_running_in_cluster(
                'non-existant-session'
            )
            assert result is False
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'oh_event',
                '{"request_id": "'
                + str(id)
                + '", "sids": ["non-existant-session"], "message_type": "is_session_running"}',
            )


@pytest.mark.asyncio
async def test_session_is_running_in_cluster():
    id = uuid4()
    sio = get_mock_sio(
        GetMessageMock(
            {
                'request_id': str(id),
                'sids': ['existing-session'],
                'message_type': 'session_is_running',
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
            result = await session_manager.is_agent_loop_running_in_cluster(
                'existing-session'
            )
            assert result is True
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'oh_event',
                '{"request_id": "'
                + str(id)
                + '", "sids": ["existing-session"], "message_type": "is_session_running"}',
            )


@pytest.mark.asyncio
async def test_init_new_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    is_agent_loop_running_in_cluster_mock = AsyncMock()
    is_agent_loop_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.1),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.is_agent_loop_running_in_cluster',
            is_agent_loop_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData()
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData()
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
    is_agent_loop_running_in_cluster_mock = AsyncMock()
    is_agent_loop_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.is_agent_loop_running_in_cluster',
            is_agent_loop_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData()
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData()
            )
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData()
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
    is_agent_loop_running_in_cluster_mock = AsyncMock()
    is_agent_loop_running_in_cluster_mock.return_value = True
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.is_agent_loop_running_in_cluster',
            is_agent_loop_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation(
                'new-session-id', 'new-session-id', ConversationInitData()
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
    is_agent_loop_running_in_cluster_mock = AsyncMock()
    is_agent_loop_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.is_agent_loop_running_in_cluster',
            is_agent_loop_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData()
            )
            await session_manager.join_conversation(
                'new-session-id', 'connection-id', ConversationInitData()
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
    is_agent_loop_running_in_cluster_mock = AsyncMock()
    is_agent_loop_running_in_cluster_mock.return_value = True
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager.is_agent_loop_running_in_cluster',
            is_agent_loop_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation(
                'new-session-id', 'connection-id', ConversationInitData()
            )
            await session_manager.send_to_event_stream(
                'connection-id', {'event_type': 'some_event'}
            )
    assert sio.manager.redis.publish.await_count == 1
    sio.manager.redis.publish.assert_called_once_with(
        'oh_event',
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
            session_manager.local_connection_id_to_session_id.update(
                {
                    'conn1': 'session1',
                    'conn2': 'session1',
                    'conn3': 'session2',
                    'conn4': 'session2',
                }
            )

            await session_manager._on_close_session('session1')

            remaining_connections = session_manager.local_connection_id_to_session_id
            assert 'conn1' not in remaining_connections
            assert 'conn2' not in remaining_connections
            assert 'conn3' in remaining_connections
            assert 'conn4' in remaining_connections
            assert remaining_connections['conn3'] == 'session2'
            assert remaining_connections['conn4'] == 'session2'
