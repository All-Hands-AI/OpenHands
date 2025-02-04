"""Test Ctrl+C handling in BashSession."""

import os
import time

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import BashSession


def test_ctrl_c_handling():
    """Test that Ctrl+C is handled correctly."""
    # Create a temporary directory for testing
    work_dir = '/tmp/test_bash_ctrl_c'
    os.makedirs(work_dir, exist_ok=True)

    # Initialize bash session with a short no_change_timeout
    bash = BashSession(work_dir=work_dir, no_change_timeout_seconds=2)
    bash.initialize()

    try:
        # Start a long-running process
        action = CmdRunAction(command='while true; do sleep 1; done')
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)

        # Wait a moment for the process to start
        time.sleep(1)

        # Try to run another command - this should fail
        action = CmdRunAction(command='echo test')
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1, 'Should not be able to run commands while running'

        # Send Ctrl+C
        action = CmdRunAction(command='C-c', is_input=True)
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 130, 'Process interrupted by Ctrl+C should return 130'

        # Run another command
        action = CmdRunAction(command='echo test')
        obs = bash.execute(action)
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0, 'Should be able to run commands after Ctrl+C'
        assert 'test' in obs.content, 'Command output should be visible'

    finally:
        bash.close()
