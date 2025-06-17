"""
Unit tests for CLI runtime signal handling, specifically testing Windows compatibility.
"""

import signal
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime, _get_signal_constant
from openhands.storage import get_file_store


class TestSignalHandling:
    """Test signal handling in CLI runtime."""

    def test_get_signal_constant_existing(self):
        """Test that _get_signal_constant returns existing signals."""
        # SIGTERM should exist on all platforms
        sigterm = _get_signal_constant('SIGTERM')
        assert sigterm is not None
        assert sigterm == signal.SIGTERM

    def test_get_signal_constant_nonexistent(self):
        """Test that _get_signal_constant returns None for non-existent signals."""
        fake_signal = _get_signal_constant('FAKE_SIGNAL_THAT_DOES_NOT_EXIST')
        assert fake_signal is None

    def test_get_signal_constant_sigkill(self):
        """Test SIGKILL handling - exists on Unix, may not exist on Windows."""
        sigkill = _get_signal_constant('SIGKILL')

        if sys.platform == 'win32':
            # On Windows, SIGKILL may not exist
            # This test just ensures no exception is raised
            assert sigkill is None or isinstance(sigkill, int)
        else:
            # On Unix-like systems, SIGKILL should exist
            assert sigkill is not None
            assert sigkill == signal.SIGKILL

    @patch('sys.platform', 'win32')
    def test_safe_terminate_process_windows_terminate(self):
        """Test Windows process termination with terminate signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object
            mock_process = MagicMock()
            mock_process.pid = 12345

            # Test with SIGTERM (should call terminate)
            sigterm = _get_signal_constant('SIGTERM')
            runtime._safe_terminate_process(mock_process, signal_to_send=sigterm)

            mock_process.terminate.assert_called_once()
            mock_process.kill.assert_not_called()

    @patch('sys.platform', 'win32')
    @patch('openhands.runtime.impl.cli.cli_runtime._get_signal_constant')
    def test_safe_terminate_process_windows_kill(self, mock_get_signal):
        """Test Windows process termination with kill signal."""
        # Mock SIGKILL to exist for this test
        mock_sigkill = 9
        mock_get_signal.side_effect = (
            lambda name: mock_sigkill if name == 'SIGKILL' else None
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object
            mock_process = MagicMock()
            mock_process.pid = 12345

            # Test with SIGKILL (should call kill)
            runtime._safe_terminate_process(mock_process, signal_to_send=mock_sigkill)

            mock_process.kill.assert_called_once()
            mock_process.terminate.assert_not_called()

    @patch('sys.platform', 'linux')
    def test_safe_terminate_process_unix_with_signals(self):
        """Test Unix process termination uses signals."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object
            mock_process = MagicMock()
            mock_process.pid = 12345

            # Mock os.getpgid and os.killpg to avoid actual signal sending
            with (
                patch('os.getpgid', return_value=12345),
                patch('os.killpg') as mock_killpg,
            ):
                sigterm = _get_signal_constant('SIGTERM')
                runtime._safe_terminate_process(mock_process, signal_to_send=sigterm)

                # Should use killpg with the signal
                mock_killpg.assert_called_once_with(12345, sigterm)

    def test_safe_terminate_process_none_signal(self):
        """Test that None signal defaults to SIGTERM on Unix."""
        if sys.platform == 'win32':
            pytest.skip('This test is for Unix-like systems')

        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object
            mock_process = MagicMock()
            mock_process.pid = 12345

            # Mock os.getpgid and os.killpg
            with (
                patch('os.getpgid', return_value=12345),
                patch('os.killpg') as mock_killpg,
            ):
                # Call with None signal
                runtime._safe_terminate_process(mock_process, signal_to_send=None)

                # Should default to SIGTERM
                expected_signal = _get_signal_constant('SIGTERM') or signal.SIGTERM
                mock_killpg.assert_called_once_with(12345, expected_signal)

    def test_safe_terminate_process_no_pid(self):
        """Test that method handles process with no PID gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object without PID
            mock_process = MagicMock()
            mock_process.pid = None

            # Should return early without error
            runtime._safe_terminate_process(mock_process)

            # No methods should be called
            mock_process.terminate.assert_not_called()
            mock_process.kill.assert_not_called()

    @patch('sys.platform', 'win32')
    def test_safe_terminate_process_windows_exception(self):
        """Test Windows process termination handles exceptions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            config.workspace_base = temp_dir
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)

            runtime = CLIRuntime(
                config=config, event_stream=event_stream, sid='test_session'
            )

            # Mock process object that raises exception
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.terminate.side_effect = Exception('Test exception')

            # Should not raise exception
            runtime._safe_terminate_process(mock_process)

            mock_process.terminate.assert_called_once()
