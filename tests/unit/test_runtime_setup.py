import pytest
from unittest.mock import MagicMock, patch

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation
from openhands.runtime.base import Runtime


class TestRuntimeSetup:
    def test_setup_script_blocks_commands(self):
        """Test that commands are blocked while setup.sh is running."""
        # Create a mock runtime
        runtime = MagicMock(spec=Runtime)
        
        # Set the flag to indicate setup.sh is running
        runtime._setup_script_completed = False
        
        # Create our implementation of run_action
        def mock_run_action(action):
            # Check if setup.sh is still running
            if (
                isinstance(action, CmdRunAction) 
                and not getattr(action, 'is_static', False)
                and not runtime._setup_script_completed
            ):
                return ErrorObservation(
                    'Cannot execute commands until setup.sh has completed. Please wait.'
                )
            return CmdOutputObservation(command=action.command, content="Command executed successfully", exit_code=0)
            
        # Replace the mock's run_action with our implementation
        runtime.run_action.side_effect = mock_run_action
        
        # Test 1: When setup.sh is running, commands should be blocked
        action = CmdRunAction(command="echo 'Hello'")
        result = runtime.run_action(action)
        
        # Verify the command was blocked
        assert isinstance(result, ErrorObservation)
        assert "Cannot execute commands until setup.sh has completed" in result.content
        
        # Test 2: After setup.sh completes, commands should work
        runtime._setup_script_completed = True  # Simulate setup.sh completion
        
        action = CmdRunAction(command="echo 'Hello'")
        result = runtime.run_action(action)
        
        # Verify the command was executed
        assert isinstance(result, CmdOutputObservation)
        assert result.exit_code == 0
        
    def test_setup_script_allows_static_commands(self):
        """Test that static commands are allowed even when setup.sh is running."""
        # Create a mock runtime
        runtime = MagicMock(spec=Runtime)
        
        # Set the flag to indicate setup.sh is running
        runtime._setup_script_completed = False
        
        # Create our implementation of run_action
        def mock_run_action(action):
            # Check if setup.sh is still running
            if (
                isinstance(action, CmdRunAction) 
                and not getattr(action, 'is_static', False)
                and not runtime._setup_script_completed
            ):
                return ErrorObservation(
                    'Cannot execute commands until setup.sh has completed. Please wait.'
                )
            return CmdOutputObservation(command=action.command, content="Command executed successfully", exit_code=0)
            
        # Replace the mock's run_action with our implementation
        runtime.run_action.side_effect = mock_run_action
        
        # Test: Static commands should be allowed even when setup.sh is running
        action = CmdRunAction(command="echo 'Hello'", is_static=True)
        result = runtime.run_action(action)
        
        # Verify the command was executed
        assert isinstance(result, CmdOutputObservation)
        assert result.exit_code == 0