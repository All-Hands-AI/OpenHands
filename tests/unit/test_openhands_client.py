import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.runtime.plugins.agent_skills.openhands_client import (
    OpenhandsClient,
    message_to_remote_OH,
)


@pytest.mark.asyncio
async def test_init_with_conversation_id():
    """
    When conversation_id is specified in the constructor, _get_conversation_id should not be called.
    """
    with patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.openhands_client.requests.post'
    ) as mock_post:
        client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
        mock_post.assert_not_called()
        assert client.conversation_id == 'abc123'


@pytest.mark.asyncio
async def test_init_without_conversation_id():
    """
    When  conversation_id is not specified in the constructor, _get_conversation_id should be called.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {'conversation_id': 'xyz789'}
    mock_response.raise_for_status.return_value = None

    with patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.openhands_client.requests.post',
        return_value=mock_response,
    ) as mock_post:
        client = OpenhandsClient('http://dummy_url')
        mock_post.assert_called_once_with('http://dummy_url/api/conversations', json={})
        assert client.conversation_id == 'xyz789'


@pytest.mark.asyncio
async def test_connect():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.sio.connect = AsyncMock()

    await client.connect()
    client.sio.connect.assert_awaited_once_with(
        'http://dummy_url?conversation_id=abc123'
    )


@pytest.mark.asyncio
async def test_close():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.sio.disconnect = AsyncMock()

    await client.close()
    client.sio.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_wait_ready_success():
    """
    When history_loaded=True and agent_ready=True, wait_ready should return True.
    """
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.history_loaded = False
    client.agent_ready = False

    async def make_ready():
        await asyncio.sleep(0.1)
        client.history_loaded = True
        client.agent_ready = True

    wait_task = asyncio.create_task(client.wait_ready())
    ready_task = asyncio.create_task(make_ready())

    done, pending = await asyncio.wait({wait_task, ready_task}, timeout=3)
    assert wait_task in done, 'wait_ready should return True'
    result = wait_task.result()
    assert result is True


@pytest.mark.asyncio
async def test_wait_ready_timeout():
    """
    When history_loaded=False or agent_ready=False, wait_ready should raise an exception.
    """
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123', timeout=1)

    start_time = time.time()
    with pytest.raises(Exception) as excinfo:
        await client.wait_ready()
    end_time = time.time()

    assert 'Timeout: Server or agent is not ready' in str(excinfo.value)
    assert (end_time - start_time) >= 1


@pytest.mark.asyncio
async def test_force_ready_after_timeout():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.agent_ready = False

    # Mock asyncio.sleep to avoid actual waiting
    with patch('asyncio.sleep', side_effect=lambda x: asyncio.sleep(0)):
        task = asyncio.create_task(client._force_ready_after_timeout())
        await task

    assert client.agent_ready is True


@pytest.mark.asyncio
async def test_send_message_action_failed():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.history_loaded = False
    client.agent_ready = False

    with pytest.raises(Exception) as excinfo:
        await client.send_message_action('Hello')
    assert 'The server or agent is not ready for receiving messages.' in str(
        excinfo.value
    )


@pytest.mark.asyncio
async def test_send_message_action_success():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.history_loaded = True
    client.agent_ready = True
    client.sio.emit = AsyncMock()

    await client.send_message_action('Hello')
    client.sio.emit.assert_awaited_once_with(
        'oh_action', {'action': 'message', 'args': {'content': 'Hello'}}
    )

    assert client.agent_ready is False


@pytest.mark.asyncio
async def test_on_connect():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')

    on_connect = client.sio.handlers['/']['connect']

    await on_connect()

    assert client.history_loaded is True
    assert client.force_ready_task is not None


@pytest.mark.asyncio
async def test_on_disconnect():
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')

    on_disconnect = client.sio.handlers['/']['disconnect']

    with patch('builtins.print') as mock_print:
        await on_disconnect()
        mock_print.assert_any_call('Disconnected from server')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'initial_history_loaded, event_payload, expected_agent_state, expected_agent_ready',
    [
        (
            False,  # history_loaded is False. Test for the case where history is being loaded.
            {
                'observation': 'agent_state_changed',
                'extras': {'agent_state': 'awaiting_user_input'},
            },
            None,  # agent_state shouldn't be updated because history is being loaded.
            False,
        ),
        (
            True,
            {'observation': 'agent_state_changed', 'extras': {'agent_state': 'init'}},
            'init',
            True,
        ),
        (
            True,
            {
                'observation': 'agent_state_changed',
                'extras': {'agent_state': 'other_state'},
            },
            'other_state',
            False,
        ),
    ],
)
async def test_oh_event_state_change(
    initial_history_loaded, event_payload, expected_agent_state, expected_agent_ready
):
    """
    Test the oh_event handler for agent_state_changed event.
    """
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.history_loaded = initial_history_loaded
    client.agent_ready = False

    on_oh_event = client.sio.handlers['/']['oh_event']

    await on_oh_event(event_payload)

    assert client.agent_state == expected_agent_state
    assert client.agent_ready == expected_agent_ready


@pytest.mark.asyncio
async def test_oh_event_status_update_cancels_task():
    """
    force_ready_task should be cancelled when "status_update" is received.
    """
    client = OpenhandsClient('http://dummy_url', conversation_id='abc123')
    client.history_loaded = True
    client.force_ready_task = asyncio.create_task(asyncio.sleep(10))

    on_oh_event = client.sio.handlers['/']['oh_event']

    await on_oh_event(
        {
            'status_update': True,
            'type': 'info',
            'id': 'STATUS$STARTING_RUNTIME',
            'message': 'Starting runtime...',
        }
    )

    try:
        await client.force_ready_task
    except asyncio.CancelledError:
        pass
    assert client.force_ready_task.cancelled() is True


@pytest.mark.asyncio
async def test_message_to_remote_OH_flow():
    """
    message_to_remote_OH should call connect -> wait_ready -> send_message_action -> wait_ready -> close
    """
    with patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.OpenhandsClient.connect',
        new_callable=AsyncMock,
    ) as mock_connect, patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.OpenhandsClient.wait_ready',
        new_callable=AsyncMock,
    ) as mock_wait_ready, patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.OpenhandsClient.send_message_action',
        new_callable=AsyncMock,
    ) as mock_send_message_action, patch(
        'openhands.runtime.plugins.agent_skills.openhands_client.OpenhandsClient.close',
        new_callable=AsyncMock,
    ) as mock_close:
        mock_wait_ready.return_value = True

        await message_to_remote_OH('test', 'http://dummy_url', conversation_id='12345')

        mock_connect.assert_awaited_once()

        assert mock_wait_ready.await_count == 2
        mock_send_message_action.assert_awaited_once_with('test')
        mock_close.assert_awaited_once()
