from unittest.mock import MagicMock, Mock

import httpx
import pytest

from openhands.core.exceptions import (
    AgentRuntimeDisconnectedError,
    AgentRuntimeTimeoutError,
)
from openhands.events.action import CmdRunAction
from openhands.runtime.base import Runtime


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def runtime(mock_session):
    runtime = Mock(spec=Runtime)
    runtime.session = mock_session
    runtime.send_action_for_execution = Mock()
    return runtime


def test_runtime_timeout_error(runtime, mock_session):
    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Mock the runtime to raise a timeout error
    runtime.send_action_for_execution.side_effect = AgentRuntimeTimeoutError(
        'Runtime failed to return execute_action before the requested timeout of 120s'
    )

    # Verify that the error message indicates a timeout
    with pytest.raises(AgentRuntimeTimeoutError) as exc_info:
        runtime.send_action_for_execution(action)

    assert (
        str(exc_info.value)
        == 'Runtime failed to return execute_action before the requested timeout of 120s'
    )


@pytest.mark.parametrize(
    'status_code,expected_message',
    [
        (404, 'Runtime is not responding. This may be temporary, please try again.'),
        (
            502,
            'Runtime is temporarily unavailable. This may be due to a restart or network issue, please try again.',
        ),
    ],
)
def test_runtime_disconnected_error(
    runtime, mock_session, status_code, expected_message
):
    # Mock the request to return the specified status code
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            'mock_error', request=MagicMock(), response=mock_response
        )
    )
    mock_response.json = Mock(
        return_value={
            'observation': 'run',
            'content': 'test',
            'extras': {'command_id': 'test_id', 'command': 'test command'},
        }
    )

    # Mock the runtime to raise the error
    runtime.send_action_for_execution.side_effect = AgentRuntimeDisconnectedError(
        expected_message
    )

    # Create a command action
    action = CmdRunAction(command='test command')
    action.set_hard_timeout(120)

    # Verify that the error message is correct
    with pytest.raises(AgentRuntimeDisconnectedError) as exc_info:
        runtime.send_action_for_execution(action)

    assert str(exc_info.value) == expected_message
