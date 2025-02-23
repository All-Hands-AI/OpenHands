import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from openhands.core.cli import main


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
        assert mock_controller_instance.status_callback is None
        yield mock_controller_instance


@pytest.mark.asyncio
@patch('builtins.input', return_value='')
async def test_cli_session_id_output(mock_runtime, mock_agent, mock_controller, capsys):
    # display sid in console when starting
    await main(asyncio.get_event_loop())
    captured = capsys.readouterr()
    assert 'Session ID:' in captured.out
