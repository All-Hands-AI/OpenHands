import asyncio
import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.server.conversation_manager.standalone_conversation_manager import (
    StandaloneConversationManager,
)
from openhands.server.monitoring import MonitoringListener
from openhands.server.session.conversation_init_data import ConversationInitData
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
async def test_init_new_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    session_instance.agent_session.event_stream.cur_id = 1
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    is_agent_loop_running_mock = AsyncMock()
    is_agent_loop_running_mock.return_value = True
    with (
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.Session',
            mock_session,
        ),
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with StandaloneConversationManager(
            sio, OpenHandsConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            await conversation_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), 1
            )
            with (
                patch(
                    'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager.is_agent_loop_running',
                    is_agent_loop_running_mock,
                ),
            ):
                await conversation_manager.join_conversation(
                    'new-session-id',
                    'new-session-id',
                    ConversationInitData(),
                    1,
                )
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 1


@pytest.mark.asyncio
async def test_join_local_session():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    session_instance.agent_session.event_stream.cur_id = 1
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    is_agent_loop_running_mock = AsyncMock()
    is_agent_loop_running_mock.return_value = True
    with (
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.Session',
            mock_session,
        ),
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with StandaloneConversationManager(
            sio, OpenHandsConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            await conversation_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), None
            )
            with (
                patch(
                    'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager.is_agent_loop_running',
                    is_agent_loop_running_mock,
                ),
            ):
                await conversation_manager.join_conversation(
                    'new-session-id',
                    'new-session-id',
                    ConversationInitData(),
                    None,
                )
                await conversation_manager.join_conversation(
                    'new-session-id',
                    'new-session-id',
                    ConversationInitData(),
                    None,
                )
    assert session_instance.initialize_agent.call_count == 1
    assert sio.enter_room.await_count == 2


@pytest.mark.asyncio
async def test_add_to_local_event_stream():
    session_instance = AsyncMock()
    session_instance.agent_session = MagicMock()
    mock_session = MagicMock()
    mock_session.return_value = session_instance
    session_instance.agent_session.event_stream.cur_id = 1
    sio = get_mock_sio()
    get_running_agent_loops_mock = AsyncMock()
    get_running_agent_loops_mock.return_value = set()
    with (
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.Session',
            mock_session,
        ),
        patch(
            'openhands.server.conversation_manager.standalone_conversation_manager.StandaloneConversationManager.get_running_agent_loops',
            get_running_agent_loops_mock,
        ),
    ):
        async with StandaloneConversationManager(
            sio, OpenHandsConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            await conversation_manager.maybe_start_agent_loop(
                'new-session-id', ConversationInitData(), 1
            )
            await conversation_manager.join_conversation(
                'new-session-id', 'connection-id', ConversationInitData(), 1
            )
            await conversation_manager.send_to_event_stream(
                'connection-id', {'event_type': 'some_event'}
            )
    session_instance.dispatch.assert_called_once_with({'event_type': 'some_event'})


@pytest.mark.asyncio
async def test_cleanup_session_connections():
    sio = get_mock_sio()
    sio.disconnect = AsyncMock()  # Mock the disconnect method
    async with StandaloneConversationManager(
        sio, OpenHandsConfig(), InMemoryFileStore(), MonitoringListener()
    ) as conversation_manager:
        conversation_manager._local_connection_id_to_session_id.update(
            {
                'conn1': 'session1',
                'conn2': 'session1',
                'conn3': 'session2',
                'conn4': 'session2',
            }
        )

        await conversation_manager._close_session('session1')

        # Check that connections were removed from the dictionary
        remaining_connections = conversation_manager._local_connection_id_to_session_id
        assert 'conn1' not in remaining_connections
        assert 'conn2' not in remaining_connections
        assert 'conn3' in remaining_connections
        assert 'conn4' in remaining_connections
        assert remaining_connections['conn3'] == 'session2'
        assert remaining_connections['conn4'] == 'session2'

        # Check that disconnect was called for each connection
        assert sio.disconnect.await_count == 2
        sio.disconnect.assert_any_call('conn1')
        sio.disconnect.assert_any_call('conn2')
