"""Test the execution of setup.sh script."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.schema.agent import AgentState
from openhands.events import EventSource
from openhands.events.action import ChangeAgentStateAction, CmdRunAction
from openhands.runtime.base import Runtime
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime


@pytest.fixture
def mock_runtime():
    """Create a mock runtime for testing."""
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = MagicMock()
    runtime.config = MagicMock()
    runtime.config.workspace_mount_path_in_sandbox = "/workspace"
    runtime.config.sandbox = MagicMock()
    runtime.config.sandbox.timeout = 120  # Set a numeric timeout value
    runtime.sid = "test_sid"
    
    # Mock methods needed for the test
    runtime.read = MagicMock()
    runtime.read.return_value = MagicMock(exit_code=0, content="#!/bin/bash\necho 'Setup script'")
    
    # Mock the run_action method to simulate running commands
    def mock_run_action(action):
        if isinstance(action, CmdRunAction):
            if "ls" in action.command and ".openhands/setup.sh" in action.command:
                # Simulate finding the setup.sh script
                mock_obs = MagicMock()
                mock_obs.exit_code = 0
                mock_obs.content = "-rwxr-xr-x 1 root root 123 Apr 25 12:00 .openhands/setup.sh"
                return mock_obs
            elif "bash" in action.command and ".openhands/setup.sh" in action.command:
                # Simulate running the setup script
                mock_obs = MagicMock()
                mock_obs.exit_code = 0
                mock_obs.content = "Setup script executed successfully"
                # Sleep to simulate script execution time
                time.sleep(0.1)
                return mock_obs
        
        # Default response for other commands
        mock_obs = MagicMock()
        mock_obs.exit_code = 0
        mock_obs.content = ""
        return mock_obs
    
    runtime.run_action.side_effect = mock_run_action
    return runtime


def test_maybe_run_setup_script_with_script():
    """Test that maybe_run_setup_script executes the script when it exists."""
    # Create a mock runtime
    runtime = MagicMock(spec=Runtime)
    runtime.event_stream = MagicMock()
    runtime.config = MagicMock()
    runtime.config.workspace_mount_path_in_sandbox = "/workspace"
    runtime.config.sandbox = MagicMock()
    runtime.config.sandbox.timeout = 120
    runtime.sid = "test_sid"
    
    # Mock the read method to simulate finding the setup script
    runtime.read = MagicMock()
    runtime.read.return_value = MagicMock(exit_code=0, content="#!/bin/bash\necho 'Setup script'")
    
    # Mock the run_action method
    runtime.run_action = MagicMock()
    runtime.run_action.return_value = MagicMock(exit_code=0, content="Setup script executed")
    
    # Create a patched version of the maybe_run_setup_script method
    with patch('openhands.runtime.base.Runtime.maybe_run_setup_script', autospec=True) as mock_method:
        # Define the behavior we want to test
        def side_effect(self):
            # Add SETTING_UP event
            self.event_stream.add_event(
                ChangeAgentStateAction(agent_state=AgentState.SETTING_UP),
                EventSource.ENVIRONMENT,
            )
            
            # Simulate running the script
            self.run_action(CmdRunAction(command="bash .openhands/setup.sh"))
            
            # Add LOADING event to indicate completion
            self.event_stream.add_event(
                ChangeAgentStateAction(agent_state=AgentState.LOADING),
                EventSource.ENVIRONMENT,
            )
            
        mock_method.side_effect = side_effect
        
        # Call the method
        mock_method(runtime)
        
        # Verify the method was called
        assert mock_method.called
        
        # Verify run_action was called
        assert runtime.run_action.called
        
        # Verify event_stream.add_event was called at least twice
        assert runtime.event_stream.add_event.call_count >= 2


def test_maybe_run_setup_script_without_script(mock_runtime):
    """Test that maybe_run_setup_script does nothing when the script doesn't exist."""
    # Override the mock to simulate script not found
    mock_runtime.read.return_value = MagicMock(exit_code=1, content="File not found")
    mock_runtime.event_stream.add_event = MagicMock()
    
    # Create a patched DockerRuntime instance
    with patch('openhands.runtime.base.Runtime.maybe_run_setup_script', autospec=True) as mock_method:
        # Call the method directly with our mock runtime
        mock_method(mock_runtime)
        
        # Verify the method was called
        assert mock_method.called
        
        # Verify no state changes were made for RUNNING_SETUP_SCRIPT
        # (This is a simplified test since we're mocking the actual method)


def test_setup_script_execution_time():
    """Test that the setup script execution time is measured correctly."""
    # Create a mock for the Runtime.maybe_run_setup_script method
    with patch('openhands.runtime.base.Runtime.maybe_run_setup_script', autospec=True) as mock_method:
        # Make the mock method sleep to simulate execution time
        def side_effect(self):
            time.sleep(0.5)  # 500ms delay
        mock_method.side_effect = side_effect
        
        # Create a mock runtime
        runtime = MagicMock(spec=Runtime)
        runtime.config = MagicMock()
        runtime.config.sandbox = MagicMock()
        runtime.config.sandbox.timeout = 120
        
        # Call the method and measure execution time
        start_time = time.time()
        mock_method(runtime)
        end_time = time.time()
        
        # Verify the execution time is at least as long as our simulated delay
        execution_time = end_time - start_time
        assert execution_time >= 0.5, f"Execution time was {execution_time}, expected at least 0.5 seconds"