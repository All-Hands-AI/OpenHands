"""Unit tests for the setup script functionality."""

from unittest.mock import MagicMock, patch

from openhands.events.action import CmdRunAction, FileReadAction
from openhands.events.event import EventSource
from openhands.events.observation import ErrorObservation, FileReadObservation
from openhands.runtime.base import Runtime


def test_maybe_run_setup_script_executes_action():
    """Test that maybe_run_setup_script executes the action after adding it to the event stream."""
    # Create mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.read.return_value = FileReadObservation(
        content="#!/bin/bash\necho 'test'", path='.openhands/setup.sh'
    )

    # Mock the event stream
    runtime.event_stream = MagicMock()

    # Add required attributes
    runtime.status_callback = None

    # Call the actual implementation
    with patch.object(
        Runtime, 'maybe_run_setup_script', Runtime.maybe_run_setup_script
    ):
        Runtime.maybe_run_setup_script(runtime)

    # Verify that read was called with the correct action
    runtime.read.assert_called_once_with(FileReadAction(path='.openhands/setup.sh'))

    # Verify that add_event was called with the correct action and source
    runtime.event_stream.add_event.assert_called_once()
    args, kwargs = runtime.event_stream.add_event.call_args
    action, source = args
    assert isinstance(action, CmdRunAction)
    assert source == EventSource.ENVIRONMENT

    # Verify that run_action was called with the correct action
    runtime.run_action.assert_called_once()
    args, kwargs = runtime.run_action.call_args
    action = args[0]
    assert isinstance(action, CmdRunAction)
    assert (
        action.command == 'chmod +x .openhands/setup.sh && source .openhands/setup.sh'
    )


def test_maybe_run_setup_script_skips_when_file_not_found():
    """Test that maybe_run_setup_script skips execution when the setup script is not found."""
    # Create mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.read.return_value = ErrorObservation(content='File not found', error_id='')

    # Mock the event stream
    runtime.event_stream = MagicMock()

    # Call the actual implementation
    with patch.object(
        Runtime, 'maybe_run_setup_script', Runtime.maybe_run_setup_script
    ):
        Runtime.maybe_run_setup_script(runtime)

    # Verify that read was called with the correct action
    runtime.read.assert_called_once_with(FileReadAction(path='.openhands/setup.sh'))

    # Verify that add_event was not called
    runtime.event_stream.add_event.assert_not_called()

    # Verify that run_action was not called
    runtime.run_action.assert_not_called()
