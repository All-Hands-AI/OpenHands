from unittest.mock import ANY, AsyncMock, patch

import pytest
from litellm.exceptions import (
    RateLimitError,
)

from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.runtime_status import RuntimeStatus
from openhands.server.services.conversation_stats import ConversationStats
from openhands.server.session.session import Session
from openhands.storage.memory import InMemoryFileStore


@pytest.fixture
def mock_status_callback():
    return AsyncMock()


@pytest.fixture
def mock_sio():
    return AsyncMock()


@pytest.fixture
def default_llm_config():
    return LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )


@pytest.fixture
def llm_registry():
    config = OpenHandsConfig()
    return LLMRegistry(config=config)


@pytest.fixture
def conversation_stats():
    file_store = InMemoryFileStore({})
    return ConversationStats(
        file_store=file_store, conversation_id='test-conversation', user_id='test-user'
    )


@pytest.mark.asyncio
@patch('openhands.llm.llm.litellm_completion')
async def test_notify_on_llm_retry(
    mock_litellm_completion,
    mock_sio,
    default_llm_config,
    llm_registry,
    conversation_stats,
):
    config = OpenHandsConfig()
    config.set_llm_config(default_llm_config)
    session = Session(
        sid='..sid..',
        file_store=InMemoryFileStore({}),
        config=config,
        llm_registry=llm_registry,
        conversation_stats=conversation_stats,
        sio=mock_sio,
        user_id='..uid..',
    )
    session.queue_status_message = AsyncMock()

    with patch('time.sleep') as _mock_sleep:
        mock_litellm_completion.side_effect = [
            RateLimitError(
                'Rate limit exceeded', llm_provider='test_provider', model='test_model'
            ),
            {'choices': [{'message': {'content': 'Retry successful'}}]},
        ]

        # Set the retry listener on the registry
        llm_registry.retry_listner = session._notify_on_llm_retry

        # Create an LLM through the registry
        llm = llm_registry.get_llm(
            service_id='test_service',
            config=default_llm_config,
        )

        llm.completion(
            messages=[{'role': 'user', 'content': 'Hello!'}],
            stream=False,
        )

    assert mock_litellm_completion.call_count == 2
    session.queue_status_message.assert_called_once_with(
        'info', RuntimeStatus.LLM_RETRY, ANY
    )
    await session.close()


@pytest.mark.asyncio
async def test_websocket_initialization_logs_at_debug_level(
    mock_sio,
    llm_registry,
    conversation_stats,
):
    """Test that waiting for websocket connection during initialization logs at DEBUG level.

    This test verifies that the session correctly waits for the websocket client to join
    the room during initialization, and that it logs at DEBUG level (not WARNING) since
    this is expected behavior, not an error condition.
    """
    config = OpenHandsConfig()

    # Mock sio.manager.rooms to simulate no client connected initially
    mock_sio.manager.rooms.get.return_value = {}

    session = Session(
        sid='test-sid',
        file_store=InMemoryFileStore({}),
        config=config,
        llm_registry=llm_registry,
        conversation_stats=conversation_stats,
        sio=mock_sio,
        user_id='test-user',
    )

    # Mock the logger to capture log calls
    with (
        patch.object(session.logger, 'debug') as mock_debug,
        patch.object(session.logger, 'warning') as mock_warning,
    ):
        # Simulate sending an event before websocket is fully connected
        # This should trigger the waiting logic
        test_data = {'event': 'test'}

        # After first check, simulate client joining the room
        def side_effect(*args, **kwargs):
            # Return empty dict first time (no client), then return client on second call
            if mock_sio.manager.rooms.get.call_count <= 1:
                return {}
            else:
                return {'room_key': True}

        mock_sio.manager.rooms.get.side_effect = side_effect

        await session._send(test_data)

        # Verify that debug was called (not warning)
        # The message should contain "There is no listening client in the current room"
        debug_calls = [
            call
            for call in mock_debug.call_args_list
            if 'There is no listening client in the current room' in str(call)
        ]
        assert len(debug_calls) > 0, 'Expected debug log for websocket waiting'

        # Verify that warning was NOT called for this message
        warning_calls = [
            call
            for call in mock_warning.call_args_list
            if 'There is no listening client in the current room' in str(call)
        ]
        assert len(warning_calls) == 0, (
            'Should not log at WARNING level for normal initialization'
        )

    await session.close()
