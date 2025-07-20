"""Test runtime error handling for LLMMalformedActionError."""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.events.action import FileReadAction
from openhands.events.observation import ErrorObservation
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.storage import get_file_store


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def cli_runtime(temp_dir):
    """Create a CLIRuntime instance for testing."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('test', file_store)
    config = OpenHandsConfig()
    config.workspace_base = temp_dir
    runtime = CLIRuntime(config, event_stream)
    return runtime


@pytest.mark.asyncio
async def test_llm_malformed_action_error_converted_to_observation(
    cli_runtime, temp_dir
):
    """Test that LLMMalformedActionError is converted to ErrorObservation instead of stopping the agent."""
    # Initialize the runtime
    await cli_runtime.connect()

    # Create a FileReadAction that tries to access a file outside the workspace
    invalid_path = '/tmp/outside_workspace.txt'
    action = FileReadAction(path=invalid_path)

    # Mock the event stream to capture the observation
    cli_runtime.event_stream.add_event = MagicMock()

    # Execute the action through _handle_action
    await cli_runtime._handle_action(action)

    # Verify that add_event was called with an ErrorObservation
    cli_runtime.event_stream.add_event.assert_called_once()
    call_args = cli_runtime.event_stream.add_event.call_args
    observation = call_args[0][0]  # First argument is the observation

    # Verify it's an ErrorObservation with the expected error message
    assert isinstance(observation, ErrorObservation)
    assert 'Invalid path:' in observation.content
    assert invalid_path in observation.content
    assert temp_dir in observation.content


@pytest.mark.asyncio
async def test_llm_malformed_action_error_path_traversal(cli_runtime, temp_dir):
    """Test that path traversal attempts are converted to ErrorObservation."""
    # Initialize the runtime
    await cli_runtime.connect()

    # Create a FileReadAction that tries path traversal
    traversal_path = os.path.join(temp_dir, '..', 'outside.txt')
    action = FileReadAction(path=traversal_path)

    # Mock the event stream to capture the observation
    cli_runtime.event_stream.add_event = MagicMock()

    # Execute the action through _handle_action
    await cli_runtime._handle_action(action)

    # Verify that add_event was called with an ErrorObservation
    cli_runtime.event_stream.add_event.assert_called_once()
    call_args = cli_runtime.event_stream.add_event.call_args
    observation = call_args[0][0]  # First argument is the observation

    # Verify it's an ErrorObservation with the expected error message
    assert isinstance(observation, ErrorObservation)
    assert 'Invalid path traversal:' in observation.content
    assert 'Path resolves outside the workspace' in observation.content


@pytest.mark.asyncio
async def test_other_exceptions_still_cause_runtime_error(cli_runtime):
    """Test that other exceptions still cause runtime errors as before."""
    # Initialize the runtime
    await cli_runtime.connect()

    # Mock the run_action method to raise a different exception
    original_run_action = cli_runtime.run_action
    cli_runtime.run_action = MagicMock(side_effect=ValueError('Some other error'))

    # Mock the event stream and status callback
    cli_runtime.event_stream.add_event = MagicMock()
    cli_runtime.set_runtime_status = MagicMock()

    # Create a valid action
    action = FileReadAction(path='test.txt')

    # Execute the action through _handle_action
    await cli_runtime._handle_action(action)

    # Verify that set_runtime_status was called (indicating a runtime error)
    cli_runtime.set_runtime_status.assert_called_once()

    # Verify that add_event was NOT called (no observation sent)
    cli_runtime.event_stream.add_event.assert_not_called()

    # Restore the original method
    cli_runtime.run_action = original_run_action
