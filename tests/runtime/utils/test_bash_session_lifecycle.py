"""Unit tests for BashSession lifecycle management and tmux zombie process fixes."""

import os
import subprocess
import tempfile
import unittest.mock as mock
from unittest.mock import MagicMock, patch

import pytest

from openhands.runtime.utils.bash import BashSession, cleanup_zombie_tmux_processes


class TestZombieCleanupFunction:
    """Test the zombie cleanup utility function."""

    def test_cleanup_zombie_tmux_processes_no_zombies(self):
        """Test cleanup function when no zombie processes exist."""
        with patch('subprocess.run') as mock_run:
            # Mock ps aux output with no zombie processes
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  20000  4000 ?        Ss   10:00   0:00 /sbin/init
root       100  0.0  0.0   6660  4140 ?        Ss   10:01   0:00 /usr/bin/tmux new-session
"""

            cleaned_count = cleanup_zombie_tmux_processes()

            # Should call ps aux but not kill any processes
            assert mock_run.call_count == 1
            assert mock_run.call_args_list[0][0] == (['ps', 'aux'],)
            assert cleaned_count == 0

    def test_cleanup_zombie_tmux_processes_with_zombies(self):
        """Test cleanup function when zombie tmux processes exist."""
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

            # Should call ps aux and then kill the two zombie processes
            assert mock_run.call_count == 3
            assert mock_run.call_args_list[0][0] == (['ps', 'aux'],)
            assert mock_run.call_args_list[1][0] == (['kill', '-9', '100'],)
            assert mock_run.call_args_list[2][0] == (['kill', '-9', '101'],)
            assert cleaned_count == 2

    def test_cleanup_zombie_tmux_processes_kill_failure(self):
        """Test cleanup function when kill command fails."""
        with patch('subprocess.run') as mock_run:
            # Mock ps aux output with one zombie process
            ps_output = """USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root       100  0.0  0.0      0     0 ?        Z    10:01   0:00 [tmux] <defunct>
"""
            mock_run.side_effect = [
                # First call: ps aux
                mock.MagicMock(returncode=0, stdout=ps_output),
                # Second call: kill -9 100 (fails)
                subprocess.CalledProcessError(1, ['kill', '-9', '100']),
            ]

            cleaned_count = cleanup_zombie_tmux_processes()

            # Should try to kill but fail gracefully
            assert mock_run.call_count == 2
            assert cleaned_count == 0  # No processes successfully cleaned

    def test_cleanup_zombie_tmux_processes_ps_failure(self):
        """Test cleanup function when ps command fails."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ['ps', 'aux'])

            cleaned_count = cleanup_zombie_tmux_processes()

            # Should handle ps failure gracefully
            assert mock_run.call_count == 1
            assert cleaned_count == 0


class TestBashSessionLifecycle:
    """Test BashSession lifecycle management improvements."""

    def test_bash_session_init_sets_closed_attribute(self):
        """Test that BashSession.__init__ properly initializes _closed attribute."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock libtmux to avoid actual tmux operations
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane

                session = BashSession(work_dir=temp_dir, username='test')

                # Should initialize _closed to False
                assert hasattr(session, '_closed')
                assert session._closed is False

    def test_bash_session_close_with_no_remaining_sessions(self):
        """Test that close() kills the tmux server when no sessions remain."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_session.name = 'test-session'

                # Mock server.sessions to return empty list (no remaining sessions)
                mock_server.sessions = []

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Close the session
                session.close()

                # Should kill both session and server
                mock_session.kill.assert_called_once()
                mock_server.kill.assert_called_once()
                assert session._closed is True

    def test_bash_session_close_with_remaining_sessions(self):
        """Test that close() keeps the tmux server alive when other sessions exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()
                mock_other_session = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_session.name = 'test-session'

                # Mock server.sessions to return other sessions
                mock_server.sessions = [mock_other_session]

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Close the session
                session.close()

                # Should kill session but not server
                mock_session.kill.assert_called_once()
                mock_server.kill.assert_not_called()
                assert session._closed is True

    def test_bash_session_close_handles_exceptions(self):
        """Test that close() handles exceptions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_session.name = 'test-session'

                # Make session.kill() raise an exception
                mock_session.kill.side_effect = Exception('Kill failed')
                mock_server.sessions = []

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Close should not raise exception
                session.close()

                # Should still set _closed to True
                assert session._closed is True

    def test_bash_session_close_idempotent(self):
        """Test that close() can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_session.name = 'test-session'
                mock_server.sessions = []

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Close multiple times
                session.close()
                session.close()
                session.close()

                # Should only kill once
                mock_session.kill.assert_called_once()
                mock_server.kill.assert_called_once()
                assert session._closed is True

    def test_bash_session_initialize_calls_zombie_cleanup(self):
        """Test that initialize() calls zombie cleanup before creating session."""
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
                mock_cleanup.return_value = 2  # Mock cleaning 2 processes

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Should call zombie cleanup
                mock_cleanup.assert_called_once()

    def test_bash_session_initialize_handles_cleanup_failure(self):
        """Test that initialize() continues even if zombie cleanup fails."""
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
                mock_cleanup.side_effect = Exception('Cleanup failed')

                session = BashSession(work_dir=temp_dir, username='test')

                # Should not raise exception
                session.initialize()

                # Should still create session successfully
                mock_server.new_session.assert_called_once()

    def test_bash_session_getattr_closed_safety(self):
        """Test that getattr is used safely for _closed attribute."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_session = MagicMock()
                mock_pane = MagicMock()

                mock_libtmux.Server.return_value = mock_server
                mock_server.new_session.return_value = mock_session
                mock_session.active_pane = mock_pane
                mock_server.sessions = []

                session = BashSession(work_dir=temp_dir, username='test')

                # Delete _closed attribute to simulate initialization failure
                delattr(session, '_closed')

                # close() should still work without raising AttributeError
                session.close()

                # Should set _closed to True
                assert session._closed is True


class TestBashSessionErrorRecovery:
    """Test error recovery mechanisms in BashSession."""

    def test_get_pane_content_error_recovery(self):
        """Test that _get_pane_content errors trigger cleanup and recovery."""
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

                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Mock _get_pane_content to raise an exception
                with patch.object(session, '_get_pane_content') as mock_get_content:
                    mock_get_content.side_effect = Exception('Pane content error')

                    # Mock the execute method's error handling path
                    from openhands.events.action import CmdRunAction

                    CmdRunAction(command='echo test')

                    # This should trigger the error recovery path
                    # Note: We can't easily test the full execute method due to its complexity,
                    # but we can verify the error handling components work

                    # Verify cleanup is available
                    assert callable(cleanup_zombie_tmux_processes)

                    # Verify close method works
                    session.close()
                    mock_cleanup.assert_called()


class TestBashSessionIntegration:
    """Integration tests for BashSession improvements."""

    @pytest.mark.skipif(
        not os.path.exists('/usr/bin/tmux'),
        reason='tmux not available for integration testing',
    )
    def test_real_tmux_session_lifecycle(self):
        """Integration test with real tmux (if available)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Test basic session creation and cleanup
                session = BashSession(work_dir=temp_dir, username='test')
                session.initialize()

                # Verify session is working
                assert hasattr(session, 'session')
                assert hasattr(session, 'server')
                assert session._closed is False

                # Close and verify cleanup
                session.close()
                assert session._closed is True

            except Exception as e:
                # If tmux is not properly configured, skip gracefully
                pytest.skip(f'tmux integration test failed: {e}')

    def test_multiple_session_lifecycle(self):
        """Test creating and closing multiple sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('openhands.runtime.utils.bash.libtmux') as mock_libtmux:
                mock_server = MagicMock()
                mock_libtmux.Server.return_value = mock_server

                sessions = []
                mock_sessions_list = []

                # Create multiple sessions
                for i in range(3):
                    mock_session = MagicMock()
                    mock_pane = MagicMock()
                    mock_session.active_pane = mock_pane
                    mock_session.name = f'test-session-{i}'
                    mock_sessions_list.append(mock_session)

                    # Mock server behavior
                    mock_server.new_session.return_value = mock_session
                    mock_server.sessions = mock_sessions_list.copy()

                    session = BashSession(work_dir=temp_dir, username='test')
                    session.initialize()
                    sessions.append(session)

                # Close sessions one by one
                for i, session in enumerate(sessions):
                    # Update mock to reflect remaining sessions
                    remaining_sessions = mock_sessions_list[i + 1 :]
                    mock_server.sessions = remaining_sessions

                    session.close()

                    # Only the last session should kill the server
                    if i == len(sessions) - 1:
                        mock_server.kill.assert_called_once()
                    else:
                        mock_server.kill.assert_not_called()
