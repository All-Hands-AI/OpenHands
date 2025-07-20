import unittest
from unittest.mock import MagicMock, patch

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import BashCommandStatus, BashSession


class TestBashSessionReset(unittest.TestCase):
    """Test the reset functionality of BashSession."""

    @patch('openhands.runtime.utils.bash.libtmux.Server')
    def test_reset_terminal(self, mock_server):
        """Test that reset_terminal=True resets the terminal session."""
        # Setup mock
        mock_session = MagicMock()
        mock_window = MagicMock()
        mock_pane = MagicMock()

        mock_server.return_value.new_session.return_value = mock_session
        mock_session.new_window.return_value = mock_window
        mock_window.active_pane = mock_pane

        # Create BashSession
        bash_session = BashSession(work_dir='/tmp')

        # Mock initialize to track calls
        original_initialize = bash_session.initialize
        initialize_called = 0

        def mock_initialize():
            nonlocal initialize_called
            initialize_called += 1
            original_initialize()

        # Use setattr to avoid mypy error
        setattr(bash_session, 'initialize', mock_initialize)

        # Initial initialization
        bash_session.initialize()
        self.assertEqual(initialize_called, 1)

        # Create action with reset_terminal=True
        action = CmdRunAction(command="echo 'test'", reset_terminal=True)

        # Execute action
        result = bash_session.execute(action)

        # Verify reset was called
        self.assertEqual(initialize_called, 2)
        self.assertIsInstance(result, CmdOutputObservation)
        self.assertIn('Terminal session has been reset', result.content)

        # Verify session.kill was called
        mock_session.kill.assert_called_once()

    @patch('openhands.runtime.utils.bash.libtmux.Server')
    def test_reset_terminal_recovers_from_stuck_session(self, mock_server):
        """Test that reset_terminal=True can recover from a stuck session."""
        # Setup mock
        mock_session = MagicMock()
        mock_window = MagicMock()
        mock_pane = MagicMock()

        mock_server.return_value.new_session.return_value = mock_session
        mock_session.new_window.return_value = mock_window
        mock_window.active_pane = mock_pane

        # Create BashSession with mocked execute method to avoid hanging
        bash_session = BashSession(work_dir='/tmp')

        # Mock the _handle_nochange_timeout_command method to avoid hanging
        original_execute = bash_session.execute

        def mock_execute(action):
            if action.reset_terminal:
                return original_execute(action)
            else:
                # Simulate a stuck session response
                from openhands.events.observation import (
                    CmdOutputMetadata,
                    CmdOutputObservation,
                )

                metadata = CmdOutputMetadata()
                metadata.suffix = '\n[Your command is NOT executed. The previous command is still running]'
                return CmdOutputObservation(
                    command=action.command,
                    content='The previous command is still running - You CANNOT send new commands',
                    metadata=metadata,
                )

        # Use setattr to avoid mypy error
        setattr(bash_session, 'execute', mock_execute)
        bash_session.initialize()

        # Simulate a stuck session by setting prev_status to CONTINUE
        bash_session.prev_status = BashCommandStatus.CONTINUE

        # First try a normal command - should fail
        action1 = CmdRunAction(command="echo 'test'")
        result1 = bash_session.execute(action1)

        # Verify it failed with the expected message
        self.assertIn('The previous command is still running', result1.content)

        # Now try with reset_terminal=True
        action2 = CmdRunAction(command="echo 'test'", reset_terminal=True)
        result2 = bash_session.execute(action2)

        # Verify reset worked
        self.assertIn('Terminal session has been reset', result2.content)

        # Verify session.kill was called
        mock_session.kill.assert_called_once()

        # Verify prev_status was reset
        self.assertNotEqual(bash_session.prev_status, BashCommandStatus.CONTINUE)


if __name__ == '__main__':
    unittest.main()
