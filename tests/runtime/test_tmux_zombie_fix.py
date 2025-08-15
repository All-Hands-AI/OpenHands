"""Tests for tmux zombie process fix in bash session management."""

import tempfile
import unittest.mock as mock
from unittest.mock import MagicMock, patch

import pytest
from conftest import _close_test_runtime, _load_runtime

from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation
from openhands.runtime.utils.bash import cleanup_zombie_tmux_processes


class TestTmuxZombieFix:
    """Test the tmux zombie process fix functionality."""

    def test_cleanup_zombie_tmux_processes_function(self):
        """Test the zombie cleanup utility function."""
        with patch('subprocess.run') as mock_run:
            # Mock ps aux output with zombie tmux processes
            ps_output = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  20000  4000 ?        Ss   10:00   0:00 /sbin/init
root       100  0.0  0.0      0     0 ?        Z    10:01   0:00 [tmux] <defunct>
root       101  0.0  0.0      0     0 ?        Z    10:02   0:00 [tmux: server] <defunct>
root       200  0.0  0.0   6660  4140 ?        Ss   10:03   0:00 /usr/bin/tmux new-session
"""
            mock_run.side_effect = [
                # First call: ps aux
                mock.MagicMock(returncode=0, stdout=ps_output),
                # Second call: kill -9 100
                mock.MagicMock(returncode=0),
                # Third call: kill -9 101
                mock.MagicMock(returncode=0),
            ]

            cleaned_count = cleanup_zombie_tmux_processes()

            # Should identify and clean 2 zombie processes
            assert cleaned_count == 2
            assert mock_run.call_count == 3

    def test_cleanup_zombie_tmux_processes_no_zombies(self):
        """Test cleanup function when no zombies exist."""
        with patch('subprocess.run') as mock_run:
            # Mock ps aux output with no zombie processes
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  20000  4000 ?        Ss   10:00   0:00 /sbin/init
root       100  0.0  0.0   6660  4140 ?        Ss   10:01   0:00 /usr/bin/tmux new-session
"""

            cleaned_count = cleanup_zombie_tmux_processes()

            # Should find no zombies to clean
            assert cleaned_count == 0
            assert mock_run.call_count == 1

    def test_cleanup_zombie_tmux_processes_handles_errors(self):
        """Test cleanup function handles errors gracefully."""
        with patch('subprocess.run') as mock_run:
            # Mock subprocess.run to raise an exception
            mock_run.side_effect = Exception('Process error')

            # Should not raise exception
            cleaned_count = cleanup_zombie_tmux_processes()
            assert cleaned_count == 0

    def test_bash_session_close_enhanced(self):
        """Test that BashSession.close() has been enhanced with proper cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_session.name = 'test-session'

                # Import after patching
                from openhands.runtime.utils.bash import BashSession

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Test close with no remaining sessions (should kill server)
                mock_server.sessions = []
                session.close()

                # Verify both session and server are killed
                mock_session.kill.assert_called_once()
                mock_server.kill.assert_called_once()
                assert session._closed is True

    def test_bash_session_initialize_calls_cleanup(self):
        """Test that BashSession.initialize() calls zombie cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux,
                patch(
                    'openhands.runtime.utils.bash.cleanup_zombie_tmux_processes'
                ) as mock_cleanup,
            ):
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_cleanup.return_value = 1  # Mock cleaning 1 process

                # Import after patching
                from openhands.runtime.utils.bash import BashSession

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Verify cleanup was called during initialization
                mock_cleanup.assert_called_once()

    def test_bash_session_error_recovery_integration(
        self, temp_dir, runtime_cls, run_as_openhands
    ):
        """Integration test for error recovery in bash sessions."""
        # Skip for CLIRuntime as it doesn't use tmux
        if runtime_cls.__name__ == 'CLIRuntime':
            pytest.skip("CLIRuntime doesn't use tmux")

        runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
        try:
            # Test that basic commands work (verifying session is functional)
            action = CmdRunAction(command='echo "test"')
            obs = runtime.run_action(action)

            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == 0
            assert 'test' in obs.content

            # Test that the session can handle multiple commands
            action = CmdRunAction(command='pwd')
            obs = runtime.run_action(action)

            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == 0

        finally:
            _close_test_runtime(runtime)

    def test_bash_session_multiple_commands_no_hang(
        self, temp_dir, runtime_cls, run_as_openhands
    ):
        """Test that multiple commands don't cause session hangs."""
        # Skip for CLIRuntime as it doesn't use tmux
        if runtime_cls.__name__ == 'CLIRuntime':
            pytest.skip("CLIRuntime doesn't use tmux")

        runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
        try:
            # Run multiple commands in sequence
            commands = [
                'echo "command 1"',
                'ls -la',
                'echo "command 2"',
                'whoami',
                'echo "command 3"',
            ]

            for i, cmd in enumerate(commands):
                action = CmdRunAction(command=cmd)
                obs = runtime.run_action(action)

                assert isinstance(obs, CmdOutputObservation), (
                    f'Command {i + 1} failed: {cmd}'
                )
                assert obs.exit_code == 0, f'Command {i + 1} had non-zero exit: {cmd}'

        finally:
            _close_test_runtime(runtime)

    def test_bash_session_timeout_handling(
        self, temp_dir, runtime_cls, run_as_openhands
    ):
        """Test that timeout handling works correctly."""
        # Skip for CLIRuntime as it has different timeout behavior
        if runtime_cls.__name__ == 'CLIRuntime':
            pytest.skip('CLIRuntime has different timeout behavior')

        runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
        try:
            # Test a command that should timeout
            action = CmdRunAction(command='sleep 5')
            action.set_hard_timeout(1)  # 1 second timeout
            obs = runtime.run_action(action)

            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == -1  # Timeout exit code

            # Verify session is still responsive after timeout
            action = CmdRunAction(command='echo "after timeout"')
            obs = runtime.run_action(action)

            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == 0
            assert 'after timeout' in obs.content

        finally:
            _close_test_runtime(runtime)
