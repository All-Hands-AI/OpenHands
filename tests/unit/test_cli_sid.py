import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from openhands.core.cli import main
from openhands.core.schema import AgentState
from openhands.events.action import ChangeAgentStateAction


@pytest.fixture
def mock_runtime():
    with patch('openhands.core.cli.create_runtime') as mock_create_runtime:
        mock_runtime_instance = AsyncMock()
        mock_create_runtime.return_value = mock_runtime_instance
        yield mock_runtime_instance


@pytest.fixture
def mock_agent():
    with patch('openhands.core.cli.create_agent') as mock_create_agent:
        mock_agent_instance = AsyncMock()
        mock_create_agent.return_value = mock_agent_instance
        yield mock_agent_instance


@pytest.fixture
def mock_controller():
    with patch('openhands.core.cli.create_controller') as mock_create_controller:
        mock_controller_instance = AsyncMock()
        mock_create_controller.return_value = (mock_controller_instance, None)
        yield mock_controller_instance


@pytest.mark.asyncio
async def test_cli_session_id_output(mock_runtime, mock_agent, mock_controller, capsys):
    # display sid in console when it starts
    await main(asyncio.get_event_loop())
    captured = capsys.readouterr()
    assert 'Session ID:' in captured.out


@pytest.mark.asyncio
async def test_cli_runs_without_error(mock_runtime, mock_agent, mock_controller):
    await main(asyncio.get_event_loop())
    mock_runtime.connect.assert_called_once()
    mock_agent.assert_called_once()
    mock_controller.assert_called_once()
    mock_runtime.event_stream.subscribe.assert_called_once()
    mock_runtime.connect.assert_called_once()
    mock_runtime.event_stream.add_event.assert_called()


@pytest.mark.asyncio
async def test_cli_exits_on_keyboard_interrupt(
    mock_runtime, mock_agent, mock_controller
):
    with patch('openhands.core.cli.main') as mock_main:
        mock_main.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit) as e:
            await main(asyncio.get_event_loop())
        assert e.type == SystemExit
        assert e.value.code is None


@pytest.mark.asyncio
async def test_cli_handles_connection_refused_error(
    mock_runtime, mock_agent, mock_controller
):
    mock_runtime.connect.side_effect = ConnectionRefusedError('Connection refused')
    with pytest.raises(SystemExit) as e:
        await main(asyncio.get_event_loop())
    assert e.type == SystemExit
    assert e.value.code == 1


@pytest.mark.asyncio
async def test_cli_handles_generic_exception(mock_runtime, mock_agent, mock_controller):
    mock_runtime.connect.side_effect = Exception('Generic exception')
    with pytest.raises(SystemExit) as e:
        await main(asyncio.get_event_loop())
    assert e.type == SystemExit
    assert e.value.code == 1


@pytest.mark.asyncio
async def test_prompt_for_next_task_calls_read_input(
    mock_runtime, mock_agent, mock_controller, monkeypatch
):
    async def mock_read_input(_):
        return 'exit'

    monkeypatch.setattr('openhands.core.cli.read_input', mock_read_input)
    await main(asyncio.get_event_loop())
    mock_runtime.event_stream.add_event.assert_called_with(pytest.ANY, 'ENVIRONMENT')
    args, kwargs = mock_runtime.event_stream.add_event.call_args
    assert isinstance(args[0], ChangeAgentStateAction)
    assert args[0].agent_state == AgentState.STOPPED
