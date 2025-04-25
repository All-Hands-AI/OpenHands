import asyncio
import os
import time
from unittest.mock import MagicMock, call, patch

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


@pytest.mark.asyncio
async def test_setup_script_duration(mock_runtime):
    """Test that the agent state remains SETTING_UP for the full duration of setup.sh."""
    # Mock the read method to return a successful observation (not an ErrorObservation)
    mock_runtime.read.return_value = MagicMock()
    
    # Mock the status_callback attribute
    mock_runtime.status_callback = None
    
    # Create a flag to track when run_action is called and completed
    run_action_called = asyncio.Event()
    run_action_completed = asyncio.Event()
    
    # Track state changes
    state_changes = []
    
    # Store the original add_event method and create a new one that tracks state changes
    original_add_event = mock_runtime.event_stream.add_event
    
    def mock_add_event(event, source):
        if isinstance(event, ChangeAgentStateAction):
            state_changes.append((event.agent_state, time.time()))
        return original_add_event(event, source)
    
    mock_runtime.event_stream.add_event = mock_add_event
    
    # Create a patched version of time.sleep that delays execution
    original_sleep = time.sleep
    
    def patched_sleep(seconds):
        # Set the flag when run_action is called
        run_action_called.set()
        
        # Sleep for 2 seconds to simulate the script running
        original_sleep(2)
        
        # Set the flag when run_action completes
        run_action_completed.set()
    
    # Create a patched version of Runtime.run_action that simulates a long-running script
    original_run_action = mock_runtime.run_action
    
    def patched_run_action(action):
        # Sleep to simulate the script running
        patched_sleep(2)
        
        # Return a successful observation
        return CmdOutputObservation(
            command=action.command,
            content="Setup script executed successfully",
            exit_code=0,
        )
    
    mock_runtime.run_action = patched_run_action
    
    # Create a task to run the setup script using call_sync_from_async
    async def run_setup_script():
        from openhands.utils.async_utils import call_sync_from_async
        await call_sync_from_async(Runtime.maybe_run_setup_script, mock_runtime)
    
    setup_task = asyncio.create_task(run_setup_script())
    
    # Wait for run_action to be called (with a timeout)
    try:
        await asyncio.wait_for(run_action_called.wait(), timeout=5)
    except asyncio.TimeoutError:
        pytest.fail("run_action was not called within the timeout")
    
    # Wait a short time to ensure we're in the middle of the setup script
    await asyncio.sleep(0.5)
    
    # Check that the agent state was set to SETTING_UP
    assert len(state_changes) >= 1, "Expected at least one state change"
    assert state_changes[0][0] == AgentState.SETTING_UP, "First state change should be to SETTING_UP"
    
    # Check that the agent state has not been changed to LOADING yet
    assert len(state_changes) == 1, "Expected only one state change (to SETTING_UP) at this point"
    
    # Wait for run_action to complete (with a timeout)
    try:
        await asyncio.wait_for(run_action_completed.wait(), timeout=5)
    except asyncio.TimeoutError:
        pytest.fail("run_action did not complete within the timeout")
    
    # Wait for the setup task to complete
    await setup_task
    
    # Check that the agent state was set back to LOADING after completion
    assert len(state_changes) == 2, "Expected two state changes (SETTING_UP and LOADING)"
    assert state_changes[1][0] == AgentState.LOADING, "Second state change should be to LOADING"
    
    # Check that there was a delay between the state changes
    state_duration = state_changes[1][1] - state_changes[0][1]
    assert state_duration >= 1.5, f"Agent was in SETTING_UP state for only {state_duration:.2f} seconds, expected at least 1.5 seconds"


@pytest.mark.asyncio
async def test_real_setup_script_with_long_duration():
    """Test with a real setup script that sleeps for 30 seconds."""
    # Create a test directory with a setup script
    test_dir = "/tmp/test_setup_long"
    os.makedirs(f"{test_dir}/.openhands", exist_ok=True)
    
    # Create a setup script that sleeps for 30 seconds
    setup_script_path = f"{test_dir}/.openhands/setup.sh"
    with open(setup_script_path, "w") as f:
        f.write("""#!/bin/bash
echo "Starting setup script..."
echo "This script will sleep for 30 seconds..."
sleep 30
echo "Setup script completed!"
""")
    
    # Make the script executable
    os.chmod(setup_script_path, 0o755)
    
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)
    
    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream
    runtime.status_callback = None
    
    # Track state changes
    state_changes = []
    
    def mock_add_event(event, source):
        if isinstance(event, ChangeAgentStateAction):
            state_changes.append((event.agent_state, time.time()))
    
    event_stream.add_event = mock_add_event
    
    # Mock the read method to return a successful observation
    runtime.read.return_value = MagicMock()
    
    # Create a patched version of Runtime.run_action that runs the real script
    def patched_run_action(action):
        if 'setup.sh' in action.command:
            # Actually run the setup script
            start_time = time.time()
            # Replace 'source' with '.' which is more portable
            modified_command = action.command.replace('source', '.')
            os.system(f"cd {test_dir} && {modified_command}")
            end_time = time.time()
            
            # Return a successful observation
            return CmdOutputObservation(
                command=action.command,
                content=f"Setup script executed successfully in {end_time - start_time:.2f} seconds",
                exit_code=0,
            )
        else:
            # For other actions, just return immediately
            return CmdOutputObservation(
                command=action.command,
                content="Command executed successfully",
                exit_code=0,
            )
    
    runtime.run_action = patched_run_action
    
    # Create a task to run the setup script using call_sync_from_async
    async def run_setup_script():
        # Save the current directory
        original_dir = os.getcwd()
        try:
            # Change to the test directory
            os.chdir(test_dir)
            
            # Run the setup script
            from openhands.utils.async_utils import call_sync_from_async
            await call_sync_from_async(Runtime.maybe_run_setup_script, runtime)
        finally:
            # Change back to the original directory
            os.chdir(original_dir)
    
    # Start timing
    start_time = time.time()
    
    # Run the setup script
    await run_setup_script()
    
    # End timing
    end_time = time.time()
    
    # Calculate the duration
    duration = end_time - start_time
    
    # Check that it took at least 29 seconds (allowing for some timing variation)
    assert duration >= 29, f"Setup script took only {duration:.2f} seconds, expected at least 29 seconds"
    
    # Check that there were exactly two state changes
    assert len(state_changes) == 2, "Expected exactly two state changes"
    
    # Check that the first state change was to SETTING_UP
    assert state_changes[0][0] == AgentState.SETTING_UP, "First state change should be to SETTING_UP"
    
    # Check that the second state change was to LOADING
    assert state_changes[1][0] == AgentState.LOADING, "Second state change should be to LOADING"
    
    # Check that the time between SETTING_UP and LOADING is at least 29 seconds
    state_duration = state_changes[1][1] - state_changes[0][1]
    assert state_duration >= 29, f"Agent was in SETTING_UP state for only {state_duration:.2f} seconds, expected at least 29 seconds"


@pytest.mark.asyncio
async def test_setup_script_non_blocking():
    """Test that the setup script execution is non-blocking."""
    # Create a mock event stream
    event_stream = MagicMock(spec=EventStream)
    
    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = event_stream
    runtime.status_callback = None
    
    # Mock the read method to return a successful observation
    runtime.read.return_value = MagicMock()
    
    # Create a flag to track when run_action is called and completed
    run_action_called = asyncio.Event()
    run_action_completed = asyncio.Event()
    
    # Track state changes
    state_changes = []
    
    def mock_add_event(event, source):
        if isinstance(event, ChangeAgentStateAction):
            state_changes.append((event.agent_state, time.time()))
    
    event_stream.add_event = mock_add_event
    
    # Create a patched version of time.sleep that delays execution
    original_sleep = time.sleep
    
    def patched_sleep(seconds):
        # Set the flag when run_action is called
        run_action_called.set()
        
        # Sleep for a longer time to simulate the script running
        original_sleep(1)
        
        # Set the flag when run_action completes
        run_action_completed.set()
    
    # Create a patched version of Runtime.run_action that simulates a long-running script
    def patched_run_action(action):
        if 'setup.sh' in action.command:
            # For the setup script, use our patched sleep
            patched_sleep(1)
        else:
            # For other actions, just return immediately
            original_sleep(0.01)
        
        # Return a successful observation
        return CmdOutputObservation(
            command=action.command,
            content="Setup script executed successfully",
            exit_code=0,
        )
    
    runtime.run_action = patched_run_action
    
    # Create a task to run the setup script using call_sync_from_async
    async def run_setup_script():
        from openhands.utils.async_utils import call_sync_from_async
        await call_sync_from_async(Runtime.maybe_run_setup_script, runtime)
    
    # Run the setup script in a background task
    setup_task = asyncio.create_task(run_setup_script())
    
    # Wait for run_action to be called
    await asyncio.wait_for(run_action_called.wait(), timeout=5)
    
    # Check that the agent state was set to SETTING_UP
    assert len(state_changes) >= 1, "Expected at least one state change"
    assert state_changes[0][0] == AgentState.SETTING_UP, "First state change should be to SETTING_UP"
    
    # Create a task that simulates other work happening while the setup script is running
    other_work_done = asyncio.Event()
    
    async def do_other_work():
        # Simulate other work happening
        await asyncio.sleep(0.5)
        other_work_done.set()
    
    other_work_task = asyncio.create_task(do_other_work())
    
    # Wait for the other work to complete
    await asyncio.wait_for(other_work_done.wait(), timeout=5)
    
    # Wait for the setup task to complete
    await setup_task
    
    # Check that the agent state was set back to LOADING after completion
    assert len(state_changes) == 2, "Expected two state changes (SETTING_UP and LOADING)"
    assert state_changes[1][0] == AgentState.LOADING, "Second state change should be to LOADING"
    
    # The test passes if we got this far without hanging
