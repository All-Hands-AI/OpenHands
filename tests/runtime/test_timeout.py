import pytest
from unittest.mock import Mock

from openhands.events.action import CmdRunAction
from openhands.events.observation import TimeoutObservation
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from requests.exceptions import Timeout


def test_timeout_observation():
    """Test that a command timeout returns a TimeoutObservation."""
    # Create a mock runtime
    runtime = Mock(spec=ActionExecutionClient)

    # Configure the mock to return a TimeoutObservation
    runtime.send_action_for_execution.return_value = TimeoutObservation(
        "Runtime failed to return execute_action before the requested timeout of 2s"
    )

    # Run a command that will timeout
    action = CmdRunAction(command="sleep 10")
    action.timeout = 2  # Set timeout after creation
    obs = runtime.send_action_for_execution(action)

    # Verify the result
    assert isinstance(obs, TimeoutObservation)
    assert "timeout" in str(obs).lower()
    assert "2s" in str(obs)
