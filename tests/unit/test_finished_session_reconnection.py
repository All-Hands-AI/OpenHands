import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.core.config.app_config import AppConfig
from openhands.core.schema import AgentState
from openhands.server.conversation_manager.standalone_conversation_manager import (
    StandaloneConversationManager,
)
from openhands.server.monitoring import MonitoringListener
from openhands.server.settings import Settings
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_sio():
    """Create a mock SocketIO server."""
    sio = MagicMock()
    sio.enter_room = AsyncMock()
    sio.manager.redis = MagicMock()
    sio.manager.redis.publish = AsyncMock()
    return sio


@pytest.fixture
def mock_session_with_finished_agent():
    """Create a mock session with a finished agent."""
    session = AsyncMock()
    session.agent_session = MagicMock()
    session.agent_session.get_state.return_value = AgentState.FINISHED
    session.agent_session.event_stream.cur_id = 1
    session.initialize_agent = AsyncMock()
    session.disconnect = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_finished_session_not_cleaned_up_on_disconnect(
    mock_sio, mock_session_with_finished_agent
):
    """Test that demonstrates the bug: finished sessions are not cleaned up on disconnect."""

    with patch(
        'openhands.server.conversation_manager.standalone_conversation_manager.Session',
        return_value=mock_session_with_finished_agent,
    ):
        async with StandaloneConversationManager(
            mock_sio, AppConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            # Step 1: Start a session
            session_id = 'test-session-id'
            connection_id = 'test-connection-id'

            # Mock that no agent loop is running initially
            with patch.object(
                conversation_manager, 'is_agent_loop_running', return_value=False
            ):
                await conversation_manager.maybe_start_agent_loop(
                    session_id,
                    Settings(),
                    user_id='test-user',
                )

            # Join the conversation
            await conversation_manager.join_conversation(
                session_id,
                connection_id,
                Settings(),
                user_id='test-user',
                github_user_id=None,
                mnemonic=None,
                system_prompt=None,
                user_prompt=None,
                mcp_disable=None,
                knowledge_base=None,
            )

            # Verify session was created
            assert session_id in conversation_manager._local_agent_loops_by_sid
            assert (
                connection_id in conversation_manager._local_connection_id_to_session_id
            )

            # Step 2: Simulate agent finishing (session now has FINISHED state)
            # This is already set up in the mock

            # Step 3: User disconnects
            await conversation_manager.disconnect_from_session(connection_id)

            # ISSUE: Session should be cleaned up since agent is FINISHED and no connections remain
            # But currently it's not being cleaned up

            # This assertion will FAIL with current implementation, demonstrating the bug
            assert (
                session_id not in conversation_manager._local_agent_loops_by_sid
            ), 'BUG: Finished session should be cleaned up when last connection disconnects'


@pytest.mark.asyncio
async def test_finished_session_reconnection_creates_new_session_not_starting_up(
    mock_sio, mock_session_with_finished_agent
):
    """Test that reconnecting to a finished session should create a new session, not get stuck."""

    # Mock get_connections to return empty when checking for remaining connections
    async def mock_get_connections(filter_to_sids=None):
        return {}

    with patch(
        'openhands.server.conversation_manager.standalone_conversation_manager.Session',
        return_value=mock_session_with_finished_agent,
    ):
        async with StandaloneConversationManager(
            mock_sio, AppConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            conversation_manager.get_connections = mock_get_connections

            session_id = 'test-session-id'
            connection_id_1 = 'test-connection-id-1'
            connection_id_2 = 'test-connection-id-2'

            # Step 1: Start session and finish it
            with patch.object(
                conversation_manager, 'is_agent_loop_running', return_value=False
            ):
                await conversation_manager.maybe_start_agent_loop(
                    session_id,
                    Settings(),
                    user_id='test-user',
                )

            await conversation_manager.join_conversation(
                session_id,
                connection_id_1,
                Settings(),
                user_id='test-user',
                github_user_id=None,
                mnemonic=None,
                system_prompt=None,
                user_prompt=None,
                mcp_disable=None,
                knowledge_base=None,
            )

            # Step 2: User disconnects from finished session
            await conversation_manager.disconnect_from_session(connection_id_1)

            # Step 3: User reconnects to the same session
            # This should work properly and not get stuck in "starting up" state

            # The key issue: is_agent_loop_running returns True because session still exists
            # but the agent is in FINISHED state, so new initialization is skipped
            loop_running_before_fix = await conversation_manager.is_agent_loop_running(
                session_id
            )

            # With the current bug, this returns True (session exists but is finished)
            # After the fix, this should return False (finished sessions should be cleaned up)
            print(f'Agent loop running (before fix): {loop_running_before_fix}')

            # Try to join again - this should work without getting stuck
            event_stream = await conversation_manager.join_conversation(
                session_id,
                connection_id_2,
                Settings(),
                user_id='test-user',
                github_user_id=None,
                mnemonic=None,
                system_prompt=None,
                user_prompt=None,
                mcp_disable=None,
                knowledge_base=None,
            )

            # Should successfully create event stream
            assert event_stream is not None

            # The session should be properly reinitialized
            # (This test will help us verify the fix works)


@pytest.mark.asyncio
async def test_memory_usage_stability_with_multiple_finish_reconnect_cycles(
    mock_sio, mock_session_with_finished_agent
):
    """Test that memory usage remains stable over multiple finish-reconnect cycles."""

    async def mock_get_connections(filter_to_sids=None):
        return {}

    with patch(
        'openhands.server.conversation_manager.standalone_conversation_manager.Session',
        return_value=mock_session_with_finished_agent,
    ):
        async with StandaloneConversationManager(
            mock_sio, AppConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            conversation_manager.get_connections = mock_get_connections

            # Track session count over multiple cycles
            session_counts = []

            for cycle in range(5):
                session_id = f'test-session-{cycle}'
                connection_id = f'test-connection-{cycle}'

                # Start session
                with patch.object(
                    conversation_manager, 'is_agent_loop_running', return_value=False
                ):
                    await conversation_manager.maybe_start_agent_loop(
                        session_id, Settings(), user_id='test-user'
                    )

                # Join and disconnect
                await conversation_manager.join_conversation(
                    session_id,
                    connection_id,
                    Settings(),
                    user_id='test-user',
                    github_user_id=None,
                    mnemonic=None,
                    system_prompt=None,
                    user_prompt=None,
                    mcp_disable=None,
                    knowledge_base=None,
                )

                await conversation_manager.disconnect_from_session(connection_id)

                # Record session count
                session_count = len(conversation_manager._local_agent_loops_by_sid)
                session_counts.append(session_count)
                print(f'Cycle {cycle}: Session count = {session_count}')

            # Memory leak test: session count should not grow indefinitely
            # After fix, finished sessions should be cleaned up
            print(f'Session counts over cycles: {session_counts}')

            # With the bug, this will grow: [1, 2, 3, 4, 5]
            # After fix, this should stay low: [0, 0, 0, 0, 0] or [1, 1, 1, 1, 1]
            assert (
                session_counts[-1] <= 1
            ), f'Memory leak detected: {session_counts[-1]} sessions remain after {len(session_counts)} cycles'


@pytest.mark.asyncio
async def test_finished_session_with_multiple_connections_not_cleaned_up_until_last_disconnect(
    mock_sio, mock_session_with_finished_agent
):
    """Test that finished sessions with multiple connections are only cleaned up when last connection disconnects."""

    # Mock get_connections to return different results
    connection_id_1 = 'test-connection-id-1'
    connection_id_2 = 'test-connection-id-2'

    async def mock_get_connections(filter_to_sids=None):
        # Return different results based on which connections remain
        if connection_id_1 in conversation_manager._local_connection_id_to_session_id:
            return {connection_id_1: 'test-session-id'}
        return {}

    with patch(
        'openhands.server.conversation_manager.standalone_conversation_manager.Session',
        return_value=mock_session_with_finished_agent,
    ):
        async with StandaloneConversationManager(
            mock_sio, AppConfig(), InMemoryFileStore(), MonitoringListener()
        ) as conversation_manager:
            conversation_manager.get_connections = mock_get_connections
            session_id = 'test-session-id'

            # Start session and join with first connection
            with patch.object(
                conversation_manager, 'is_agent_loop_running', return_value=False
            ):
                await conversation_manager.maybe_start_agent_loop(
                    session_id, Settings(), user_id='test-user'
                )

            await conversation_manager.join_conversation(
                session_id,
                connection_id_1,
                Settings(),
                user_id='test-user',
                github_user_id=None,
                mnemonic=None,
                system_prompt=None,
                user_prompt=None,
                mcp_disable=None,
                knowledge_base=None,
            )

            # Join with second connection
            await conversation_manager.join_conversation(
                session_id,
                connection_id_2,
                Settings(),
                user_id='test-user',
                github_user_id=None,
                mnemonic=None,
                system_prompt=None,
                user_prompt=None,
                mcp_disable=None,
                knowledge_base=None,
            )

            # Both connections should be tracked
            assert (
                connection_id_1
                in conversation_manager._local_connection_id_to_session_id
            )
            assert (
                connection_id_2
                in conversation_manager._local_connection_id_to_session_id
            )

            # Disconnect first connection - session should NOT be cleaned up (other connection remains)
            await conversation_manager.disconnect_from_session(connection_id_1)
            assert (
                session_id in conversation_manager._local_agent_loops_by_sid
            ), 'Session should not be cleaned up when other connections remain'

            # Disconnect second connection - session SHOULD be cleaned up (no connections remain)
            await conversation_manager.disconnect_from_session(connection_id_2)
            assert (
                session_id not in conversation_manager._local_agent_loops_by_sid
            ), 'Session should be cleaned up when last connection disconnects'


if __name__ == '__main__':
    # Run the tests to see current behavior
    asyncio.run(
        test_finished_session_not_cleaned_up_on_disconnect(
            mock_sio=MagicMock(), mock_session_with_finished_agent=AsyncMock()
        )
    )
