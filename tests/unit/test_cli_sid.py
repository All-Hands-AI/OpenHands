import asyncio
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from openhands.core.cli import main
from openhands.core.config import AppConfig
from openhands.core.schema import AgentState
from openhands.events.event import EventSource
from openhands.events.observation import AgentStateChangedObservation


@pytest.fixture
def mock_runtime():
    with patch('openhands.core.cli.create_runtime') as mock_create_runtime:
        mock_runtime_instance = AsyncMock()
        # Mock the event stream with proper async methods
        mock_runtime_instance.event_stream = AsyncMock()
        mock_runtime_instance.event_stream.subscribe = AsyncMock()
        mock_runtime_instance.event_stream.add_event = AsyncMock()
        # Mock connect method to return immediately
        mock_runtime_instance.connect = AsyncMock()
        # Ensure status_callback is None
        mock_runtime_instance.status_callback = None
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
        # Mock run_until_done to finish immediately
        mock_controller_instance.run_until_done = AsyncMock(return_value=None)
        mock_create_controller.return_value = (mock_controller_instance, None)
        yield mock_controller_instance


@pytest.fixture
def task_file(tmp_path: Path) -> Path:
    # Create a temporary file with our task
    task_file = tmp_path / 'task.txt'
    task_file.write_text('Ask me what your task is')
    return task_file


@pytest.fixture
def mock_config(task_file: Path):
    with patch('openhands.core.cli.parse_arguments') as mock_parse_args:
        # Create a proper Namespace with our temporary task file
        args = Namespace(file=str(task_file), task=None, directory=None)
        mock_parse_args.return_value = args
        with patch('openhands.core.cli.setup_config_from_args') as mock_setup_config:
            mock_config = AppConfig()
            mock_setup_config.return_value = mock_config
            yield mock_config


@pytest.mark.asyncio
async def test_cli_session_id_output(
    mock_runtime, mock_agent, mock_controller, mock_config, capsys
):
    # status_callback is set when initializing the runtime
    mock_controller.status_callback = None

    # Use input patch just for the exit command
    with patch('builtins.input', return_value='exit'):
        # Create a task for main
        main_task = asyncio.create_task(main(asyncio.get_event_loop()))

        # Give it a moment to display the session ID
        await asyncio.sleep(0.1)

        # Trigger agent state change to STOPPED to end the main loop
        event = AgentStateChangedObservation(
            content='Stop', agent_state=AgentState.STOPPED
        )
        event._source = EventSource.AGENT
        await mock_runtime.event_stream.add_event(event)

        # Wait for main to finish with a timeout
        try:
            await asyncio.wait_for(main_task, timeout=1.0)
        except asyncio.TimeoutError:
            main_task.cancel()

        # Check the output
        captured = capsys.readouterr()
        assert 'Session ID:' in captured.out
        # Also verify that our task message was processed
        assert 'Ask me what your task is' in str(mock_runtime.mock_calls)
