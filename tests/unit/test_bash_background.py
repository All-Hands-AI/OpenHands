import os
import pytest
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import BashSession

def test_ctrl_c_handling():
    """Test that Ctrl+C is handled correctly."""
    # Create a temporary directory for testing
    work_dir = "/tmp/test_bash_background"
    os.makedirs(work_dir, exist_ok=True)

    # Initialize bash session with a short no_change_timeout
    bash = BashSession(work_dir=work_dir, no_change_timeout_seconds=2)
    bash.initialize()

    try:
        # Start a long-running process
        action = CmdRunAction(command="sleep 10")
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1, "Long running process should return -1 to indicate it's still running"

        # Send Ctrl+C
        action = CmdRunAction(command="C-c", is_input=True)
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 130, "Process interrupted by Ctrl+C should return exit code 130"

        # Run another command to verify terminal is still usable
        action = CmdRunAction(command="echo 'test'")
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0, "Terminal should be usable after Ctrl+C"
        assert "test" in obs.content, "Command output should be visible after Ctrl+C"

    finally:
        bash.close()