from unittest.mock import Mock, patch

import pytest
import requests

from openhands.core.exceptions import AgentRuntimeDisconnectedError, AgentRuntimeTimeoutError
from openhands.events.action import CmdRunAction
from openhands.runtime.base import Runtime
from openhands.runtime.utils.request import RequestHTTPError


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
    action = CmdRunAction(command="test command")
    action.timeout = 120

    # Mock the runtime to raise a timeout error
    runtime.send_action_for_execution.side_effect = AgentRuntimeTimeoutError(
        "Runtime failed to return execute_action before the requested timeout of 120s"
    )

    # Verify that the error message indicates a timeout
    with pytest.raises(AgentRuntimeTimeoutError) as exc_info:
        runtime.send_action_for_execution(action)

    assert str(exc_info.value) == "Runtime failed to return execute_action before the requested timeout of 120s"


@patch('openhands.runtime.impl.action_execution.action_execution_client.send_request')
def test_runtime_reboot_error(mock_send_request, runtime, mock_session):
    # Mock the request to return 502 (indicating runtime disconnected)
    mock_response = Mock()
    mock_response.status_code = 502
    mock_response.raise_for_status = Mock(side_effect=requests.HTTPError(response=mock_response))
    mock_response.json = Mock(return_value={'observation': 'run', 'content': 'test', 'extras': {'command_id': 'test_id', 'command': 'test command'}})

    # Create a mock that raises the error
    class MockContextManager:
        def __init__(self, response):
            self.response = response

        def __enter__(self):
            raise RequestHTTPError(
                requests.HTTPError("502 error"),
                response=self.response
            )

        def __exit__(self, exc_type, exc_val, exc_tb):
            return None

    def mock_send_request_impl(*args, **kwargs):
        return MockContextManager(mock_response)

    mock_send_request.side_effect = mock_send_request_impl

    # Create a command action
    action = CmdRunAction(command="test command")
    action.timeout = 120

    # Mock the runtime to raise a reboot error
    runtime.send_action_for_execution.side_effect = AgentRuntimeDisconnectedError(
        "Runtime became unresponsive and was rebooted, potentially due to memory usage. Please try again."
    )

    # Verify that the error message indicates a reboot
    with pytest.raises(AgentRuntimeDisconnectedError) as exc_info:
        runtime.send_action_for_execution(action)

    assert str(exc_info.value) == "Runtime became unresponsive and was rebooted, potentially due to memory usage. Please try again."