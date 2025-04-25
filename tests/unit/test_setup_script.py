import pytest
from unittest.mock import MagicMock

from openhands.events import EventStream
from openhands.runtime.base import Runtime
from openhands.events.observation import ErrorObservation, CmdOutputObservation


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
        command="chmod +x .openhands/setup.sh && source .openhands/setup.sh",
        content="Setup script executed successfully",
        exit_code=0
    )
    
    # Call the method
    Runtime.maybe_run_setup_script(mock_runtime)
    
    # Verify that add_event was called at least twice (once for SETTING_UP and once for LOADING)
    assert mock_runtime.event_stream.add_event.call_count >= 2


def test_maybe_run_setup_script_when_script_does_not_exist(mock_runtime):
    """Test that the agent state is not changed when setup.sh doesn't exist."""
    # Mock the read method to return an ErrorObservation
    mock_runtime.read.return_value = ErrorObservation(content="File not found")
    
    # Call the method
    Runtime.maybe_run_setup_script(mock_runtime)
    
    # Verify that the agent state was not changed
    mock_runtime.event_stream.add_event.assert_not_called()
    
    # Verify that run_action was not called
    mock_runtime.run_action.assert_not_called()