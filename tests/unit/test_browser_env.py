"""Tests for browser environment initialization."""
import multiprocessing
import time
from unittest.mock import MagicMock, patch

import pytest
import tenacity

from openhands.core.exceptions import BrowserInitException
from openhands.runtime.browser.browser_env import BrowserEnv


def test_browser_init_success():
    """Test successful browser initialization."""
    with patch('multiprocessing.Process') as mock_process:
        # Mock process to appear alive
        mock_process_instance = MagicMock()
        mock_process_instance.is_alive.return_value = True
        mock_process.return_value = mock_process_instance

        # Mock pipe communication
        mock_pipe = MagicMock()
        mock_pipe.poll.return_value = True
        mock_pipe.recv.return_value = ('ALIVE', None)

        with patch('multiprocessing.Pipe', return_value=(mock_pipe, mock_pipe)):
            browser = BrowserEnv()
            assert browser.process.is_alive()
            browser.close()


def test_browser_init_process_failure():
    """Test browser initialization when process fails to start."""
    with patch('multiprocessing.Process') as mock_process:
        # Mock process to appear dead with error code
        mock_process_instance = MagicMock()
        mock_process_instance.is_alive.return_value = False
        mock_process_instance.exitcode = -11  # Segmentation fault
        mock_process.return_value = mock_process_instance

        with patch('multiprocessing.Pipe', return_value=(MagicMock(), MagicMock())):
            with pytest.raises(tenacity.RetryError) as exc_info:
                BrowserEnv()
            # Get the actual exception from the retry error
            retry_error = exc_info.value
            assert isinstance(retry_error.last_attempt.exception(), BrowserInitException)
            assert 'exit code -11' in str(retry_error.last_attempt.exception())


def test_browser_init_communication_failure():
    """Test browser initialization when process starts but communication fails."""
    with patch('multiprocessing.Process') as mock_process:
        # Mock process to appear alive but not responding
        mock_process_instance = MagicMock()
        mock_process_instance.is_alive.return_value = True
        mock_process.return_value = mock_process_instance

        # Mock pipe to never receive response
        mock_pipe = MagicMock()
        mock_pipe.poll.return_value = False

        with patch('multiprocessing.Pipe', return_value=(mock_pipe, mock_pipe)):
            with pytest.raises(tenacity.RetryError) as exc_info:
                BrowserEnv()
            # Get the actual exception from the retry error
            retry_error = exc_info.value
            assert isinstance(retry_error.last_attempt.exception(), BrowserInitException)
            assert 'not responding' in str(retry_error.last_attempt.exception())


def test_browser_init_error_handling():
    """Test error handling during browser initialization."""
    with patch('multiprocessing.Process') as mock_process:
        # Mock process to raise an error
        mock_process_instance = MagicMock()
        mock_process_instance.start.side_effect = OSError('Failed to start process')
        mock_process.return_value = mock_process_instance

        with patch('multiprocessing.Pipe', return_value=(MagicMock(), MagicMock())):
            with pytest.raises(OSError) as exc_info:
                BrowserEnv()
            assert 'Failed to start process' in str(exc_info.value)


def test_browser_init_retry():
    """Test that browser initialization retries on failure."""
    with patch('multiprocessing.Process') as mock_process:
        # Create a list of mock process instances that all fail
        mock_instances = []
        for _ in range(5):  # All 5 attempts fail
            instance = MagicMock()
            instance.is_alive.return_value = False
            instance.exitcode = 1
            mock_instances.append(instance)

        mock_process.side_effect = mock_instances

        # Mock pipe that never responds
        mock_pipe = MagicMock()
        mock_pipe.poll.return_value = False

        with patch('multiprocessing.Pipe', return_value=(mock_pipe, mock_pipe)):
            with pytest.raises(tenacity.RetryError) as exc_info:
                BrowserEnv()
            # Get the actual exception from the retry error
            retry_error = exc_info.value
            assert isinstance(retry_error.last_attempt.exception(), BrowserInitException)
            assert 'exit code 1' in str(retry_error.last_attempt.exception())


def test_browser_close_cleanup():
    """Test that browser close properly cleans up resources."""
    with patch('multiprocessing.Process') as mock_process:
        # Mock process
        mock_process_instance = MagicMock()
        mock_process_instance.is_alive.side_effect = [True, True, False]  # Alive then dead after join
        mock_process.return_value = mock_process_instance

        # Mock pipe
        mock_pipe = MagicMock()
        mock_pipe.poll.return_value = True
        mock_pipe.recv.return_value = ('ALIVE', None)

        with patch('multiprocessing.Pipe', return_value=(mock_pipe, mock_pipe)):
            browser = BrowserEnv()
            browser.close()

            # Verify cleanup
            assert mock_pipe.close.call_count == 2  # Both sides of pipe closed
            mock_process_instance.join.assert_called()
            mock_process_instance.terminate.assert_not_called()  # Should not need force
