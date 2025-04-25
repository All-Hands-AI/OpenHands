"""Test that setup.sh is executed properly in a real Docker runtime."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from conftest import _close_test_runtime, _load_runtime
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.action import CmdRunAction, ChangeAgentStateAction
from openhands.events import EventSource
from openhands.utils.async_utils import call_sync_from_async
from openhands.core.setup import initialize_repository_for_runtime
from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from pydantic import SecretStr


def test_setup_script_execution_in_docker_runtime(temp_dir, runtime_cls):
    """Test that setup.sh is executed properly in a real Docker runtime."""
    # Create a temporary directory for the test
    test_dir = os.path.join(temp_dir, "setup_script_test")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create .openhands directory
    openhands_dir = os.path.join(test_dir, ".openhands")
    os.makedirs(openhands_dir, exist_ok=True)
    
    # Create a setup.sh script that creates a marker file and sleeps for 20 seconds
    setup_script_path = os.path.join(openhands_dir, "setup.sh")
    with open(setup_script_path, "w") as f:
        f.write("""#!/bin/bash
echo "Starting setup script"
touch /workspace/setup_script_executed
echo "Current directory: $(pwd)"
echo "Sleeping for 20 seconds to simulate work..."
sleep 20
echo "Setup script completed"
""")
    
    # Make the script executable
    os.chmod(setup_script_path, 0o755)
    
    # Initialize the runtime
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
    )
    
    try:
        # Change to the test directory
        action = CmdRunAction(command=f'cd {test_dir}')
        obs = runtime.run_action(action)
        assert obs.exit_code == 0
        
        # Verify the setup script exists
        action = CmdRunAction(command=f'ls -la {openhands_dir}')
        obs = runtime.run_action(action)
        assert obs.exit_code == 0
        assert "setup.sh" in obs.content
        
        # Set initial agent state to LOADING
        runtime.event_stream.add_event(
            ChangeAgentStateAction(agent_state=AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )
        
        # Track agent state changes with timestamps
        state_changes = []
        
        # Create a wrapper for add_event to track state changes
        original_add_event = runtime.event_stream.add_event
        
        def add_event_wrapper(action, source):
            if isinstance(action, ChangeAgentStateAction):
                state_changes.append((action.agent_state, time.time()))
            return original_add_event(action, source)
        
        # Replace the add_event method with our wrapper
        runtime.event_stream.add_event = add_event_wrapper
        
        # Create a mock repository path for the test
        repo_path = os.path.join(test_dir, "repo")
        
        # Run the repository initialization function that calls maybe_run_setup_script
        start_time = time.time()
        initialize_repository_for_runtime(
            runtime=runtime,
            selected_repository=repo_path,
            github_token=None
        )
        end_time = time.time()
        
        # Restore the original add_event method
        runtime.event_stream.add_event = original_add_event
        
        # Verify the script execution time was at least 20 seconds
        execution_time = end_time - start_time
        assert execution_time >= 20, f"Setup script didn't run for the expected duration. Actual: {execution_time}s"
        
        # Verify the marker file was created
        action = CmdRunAction(command='ls -la /workspace/setup_script_executed')
        obs = runtime.run_action(action)
        assert obs.exit_code == 0, "Marker file was not created, setup script may not have run correctly"
        
        # Verify the agent state changes
        assert len(state_changes) >= 2, f"Expected at least two state changes, got {len(state_changes)}"
        
        # First state change should be to SETTING_UP
        assert state_changes[0][0] == AgentState.SETTING_UP, f"First state should be SETTING_UP, got {state_changes[0][0]}"
        
        # Last state change should be back to LOADING
        assert state_changes[-1][0] == AgentState.LOADING, f"Last state should be LOADING, got {state_changes[-1][0]}"
        
        # Verify that the state was SETTING_UP for the entire duration of the script execution
        setting_up_time = state_changes[0][1]
        loading_time = state_changes[-1][1]
        
        # The time difference should be at least as long as our simulated script execution
        state_duration = loading_time - setting_up_time
        assert state_duration >= 20, f"SETTING_UP state duration was {state_duration}s, expected at least 20s"
        
        # Verify no other agent states were set during script execution
        for state, timestamp in state_changes:
            if setting_up_time < timestamp < loading_time:
                assert state == AgentState.SETTING_UP, f"Expected SETTING_UP state during script execution, got {state}"
        
        logger.info("Setup script test completed successfully")
    finally:
        _close_test_runtime(runtime)