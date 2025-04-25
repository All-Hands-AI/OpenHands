from unittest.mock import MagicMock, call

import pytest

from openhands.core.schema.agent import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import ChangeAgentStateAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation
from openhands.runtime.base import Runtime


@pytest.fixture
def mock_runtime():
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = MagicMock(spec=EventStream)
    return runtime


def test_maybe_run_setup_script_when_script_exists(mock_runtime):
    """Test that the agent state is set to SETTING_UP when running setup.sh."""
    # Mock the read method to return a successful observation (not an ErrorObservation)
    mock_runtime.read.return_value = MagicMock()

    # Mock the status_callback attribute
    mock_runtime.status_callback = None

    # Mock the run_action method to return a successful observation
    mock_runtime.run_action.return_value = CmdOutputObservation(
        command='chmod +x .openhands/setup.sh && source .openhands/setup.sh',
        content='Setup script executed successfully',
        exit_code=0,
    )

    # Call the method
    Runtime.maybe_run_setup_script(mock_runtime)

    # Verify that add_event was called exactly twice
    assert mock_runtime.event_stream.add_event.call_count == 2

    # Verify the first call sets the state to SETTING_UP before running the script
    first_call = mock_runtime.event_stream.add_event.call_args_list[0]
    assert isinstance(first_call[0][0], ChangeAgentStateAction)
    assert first_call[0][0].agent_state == AgentState.SETTING_UP
    assert first_call[0][1] == EventSource.ENVIRONMENT

    # Verify the second call sets the state back to LOADING after running the script
    second_call = mock_runtime.event_stream.add_event.call_args_list[1]
    assert isinstance(second_call[0][0], ChangeAgentStateAction)
    assert second_call[0][0].agent_state == AgentState.LOADING
    assert second_call[0][1] == EventSource.ENVIRONMENT

    # Verify the order of operations: set SETTING_UP, run script, set LOADING
    mock_runtime.event_stream.add_event.assert_has_calls(
        [
            call(
                ChangeAgentStateAction(agent_state=AgentState.SETTING_UP),
                EventSource.ENVIRONMENT,
            ),
            call(
                ChangeAgentStateAction(agent_state=AgentState.LOADING),
                EventSource.ENVIRONMENT,
            ),
        ]
    )


def test_maybe_run_setup_script_when_script_does_not_exist(mock_runtime):
    """Test that the agent state is not changed when setup.sh doesn't exist."""
    # Mock the read method to return an ErrorObservation
    mock_runtime.read.return_value = ErrorObservation(content='File not found')

    # Call the method
    Runtime.maybe_run_setup_script(mock_runtime)

    # Verify that the agent state was not changed
    mock_runtime.event_stream.add_event.assert_not_called()

    # Verify that run_action was not called
    mock_runtime.run_action.assert_not_called()
