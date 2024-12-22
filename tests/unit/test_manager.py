import asyncio
import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config.app_config import AppConfig
from openhands.server.session.manager import SessionManager
from openhands.server.session.session_init_data import SessionInitData
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
    with (
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            result = await session_manager._is_session_running_in_cluster(
                'non-existant-session'
            )
            assert result is False
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'oh_event',
                '{"sid": "non-existant-session", "message_type": "is_session_running"}',
            )


@pytest.mark.asyncio
async def test_session_is_running_in_cluster():
    sio = get_mock_sio(
        GetMessageMock(
            {'sid': 'existing-session', 'message_type': 'session_is_running'}
        )
    )
    with (
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.1),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            result = await session_manager._is_session_running_in_cluster(
                'existing-session'
            )
            assert result is True
            assert sio.manager.redis.publish.await_count == 1
            sio.manager.redis.publish.assert_called_once_with(
                'oh_event',
                '{"sid": "existing-session", "message_type": "is_session_running"}',
            )


@pytest.mark.asyncio
async def test_init_new_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    is_session_running_in_cluster_mock = AsyncMock()
    is_session_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.1),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._is_session_running_in_cluster',
            is_session_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.start_agent_loop('new-session-id', SessionInitData())
            await session_manager.join_conversation('new-session-id', 'new-session-id')
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 1


@pytest.mark.asyncio
async def test_join_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    is_session_running_in_cluster_mock = AsyncMock()
    is_session_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._is_session_running_in_cluster',
            is_session_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.start_agent_loop('new-session-id', SessionInitData())
            await session_manager.join_conversation('new-session-id', 'new-session-id')
            await session_manager.join_conversation('new-session-id', 'new-session-id')
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 2


@pytest.mark.asyncio
async def test_join_cluster_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    is_session_running_in_cluster_mock = AsyncMock()
    is_session_running_in_cluster_mock.return_value = True
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._is_session_running_in_cluster',
            is_session_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation('new-session-id', 'new-session-id')
    assert session_instance.initialize_agent.call_count == 0
    assert sio.enter_room.await_count == 1


@pytest.mark.asyncio
async def test_add_to_local_event_stream():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    is_session_running_in_cluster_mock = AsyncMock()
    is_session_running_in_cluster_mock.return_value = False
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._is_session_running_in_cluster',
            is_session_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.start_agent_loop('new-session-id', SessionInitData())
            await session_manager.join_conversation('new-session-id', 'connection-id')
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
    is_session_running_in_cluster_mock = AsyncMock()
    is_session_running_in_cluster_mock.return_value = True
    with (
        patch('openhands.server.session.manager.Session', mock_session),
        patch('openhands.server.session.manager._REDIS_POLL_TIMEOUT', 0.01),
        patch(
            'openhands.server.session.manager.SessionManager._redis_subscribe',
            AsyncMock(),
        ),
        patch(
            'openhands.server.session.manager.SessionManager._is_session_running_in_cluster',
            is_session_running_in_cluster_mock,
        ),
    ):
        async with SessionManager(
            sio, AppConfig(), InMemoryFileStore()
        ) as session_manager:
            await session_manager.join_conversation('new-session-id', 'connection-id')
            await session_manager.send_to_event_stream(
                'connection-id', {'event_type': 'some_event'}
            )
    assert sio.manager.redis.publish.await_count == 1
    sio.manager.redis.publish.assert_called_once_with(
        'oh_event',
        '{"sid": "new-session-id", "message_type": "event", "data": {"event_type": "some_event"}}',
    )
