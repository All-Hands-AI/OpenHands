import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.events.action.commands import CmdRunAction
from openhands.events.observation.commands import CmdOutputObservation
from openhands.runtime.utils.bash import BashSession


@pytest.fixture
def bash_session():
    with tempfile.TemporaryDirectory() as temp_dir:
        session = BashSession(work_dir=temp_dir)
        session.initialize()
        yield session
        session.close()


def test_reset_terminal(bash_session):
    """Test that the reset_terminal parameter resets the terminal session."""
    # Create a file in the working directory
    test_file = os.path.join(bash_session.work_dir, 'test_file.txt')

    # Run a command to create the file
    action = CmdRunAction(command=f"echo 'test content' > {test_file}")
    result = bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    assert os.path.exists(test_file)

    # Run a command that would normally hang
    with patch.object(
        bash_session,
        '_get_pane_content',
        side_effect=[
            # First call returns content without PS1 prompt (simulating a hanging command)
            'Running infinite loop...',
            # Second call after reset returns content with PS1 prompt
            f'{bash_session.PS1}',
        ],
    ):
        # Simulate a hanging command by patching the _get_pane_content method
        action = CmdRunAction(
            command='while true; do sleep 1; done', reset_terminal=True
        )
        result = bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    assert 'Terminal session has been reset' in result.content

    # Verify we can run commands after reset
    action = CmdRunAction(command="echo 'After reset'")
    result = bash_session.execute(action)

    assert isinstance(result, CmdOutputObservation)
    assert 'After reset' in result.content


def test_reset_terminal_recovers_from_stuck_session(bash_session):
    """Test that reset_terminal can recover from a stuck session."""
    # Mock the execute method to simulate a stuck session
    original_execute = bash_session.execute

    def mock_execute(action):
        if not action.reset_terminal and not hasattr(bash_session, '_mock_stuck'):
            # First call - simulate a stuck command
            bash_session._mock_stuck = True
            return CmdOutputObservation(
                content='Command is stuck and not responding...',
                command=action.command,
                metadata=MagicMock(exit_code=-1),
            )
        else:
            # Reset call or subsequent calls - use the real execute method
            return original_execute(action)

    with patch.object(bash_session, 'execute', side_effect=mock_execute):
        # First command gets stuck
        action = CmdRunAction(command="echo 'This will get stuck'")
        result = bash_session.execute(action)

        assert isinstance(result, CmdOutputObservation)
        assert 'Command is stuck' in result.content
        assert result.metadata.exit_code == -1

        # Reset the terminal
        action = CmdRunAction(command="echo 'This should work'", reset_terminal=True)
        result = bash_session.execute(action)

        assert isinstance(result, CmdOutputObservation)
        assert 'Terminal session has been reset' in result.content

        # Verify we can run commands after reset
        action = CmdRunAction(command="echo 'After reset'")
        result = bash_session.execute(action)

        assert isinstance(result, CmdOutputObservation)
        assert 'After reset' in result.content
