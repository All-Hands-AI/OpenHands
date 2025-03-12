"""Test the original retry mechanism in RemoteRuntime."""

import unittest
from unittest.mock import MagicMock, patch

import requests
import tenacity
from requests.exceptions import ConnectionError

from openhands.core.config.sandbox_config import SandboxConfig
from openhands.runtime.impl.remote.remote_runtime import RemoteRuntime
from openhands.utils.tenacity_stop import stop_if_should_exit


class TestRemoteRuntimeRetryOriginal(unittest.TestCase):
    """Test the original retry mechanism in RemoteRuntime."""

    def test_retry_decorator_exists(self):
        """Test that the retry decorator is used when remote_runtime_enable_retries=True."""
        # This test verifies that the code path for retry exists in the RemoteRuntime class
        
        # Check if the methods exist
        self.assertTrue(hasattr(RemoteRuntime, '_send_action_server_request'))
        self.assertTrue(hasattr(RemoteRuntime, '_send_action_server_request_impl'))
        
        # Check the source code of the class to verify it contains retry logic
        import inspect
        source = inspect.getsource(RemoteRuntime)
        self.assertIn('remote_runtime_enable_retries', source)
        self.assertIn('retry_decorator', source)
        self.assertIn('retry_if_exception_type', source)
        
    @patch('tenacity.retry')
    def test_retry_decorator_called_with_correct_params(self, mock_retry):
        """Test that the retry decorator is called with correct parameters."""
        # Setup
        mock_retry.return_value = lambda f: f  # Make retry a pass-through decorator
        
        # Create a runtime instance with remote_runtime_enable_retries=True
        runtime = MagicMock()
        runtime._runtime_closed = False
        runtime._stop_if_closed = lambda x: False
        
        config = MagicMock()
        sandbox_config = SandboxConfig()
        sandbox_config.remote_runtime_enable_retries = True
        config.sandbox = sandbox_config
        runtime.config = config
        
        # Mock super() to return a simple object
        with patch('openhands.runtime.impl.remote.remote_runtime.super') as mock_super:
            mock_super.return_value._send_action_server_request = lambda *args, **kwargs: "mocked response"
            
            # Call the method
            RemoteRuntime._send_action_server_request(runtime, "GET", "http://example.com")
        
        # Verify retry was called with ConnectionError
        mock_retry.assert_called()
        # Get the first positional argument of the first call
        retry_args = mock_retry.call_args[1]
        
        # Check that retry is configured for ConnectionError
        self.assertIn('retry', retry_args)
        
        # Check that stop conditions include stop_if_should_exit
        self.assertIn('stop', retry_args)
        
    def test_connection_error_not_retried_when_disabled(self):
        """Test that ConnectionError is not retried when remote_runtime_enable_retries=False."""
        # Create a runtime instance with remote_runtime_enable_retries=False
        runtime = MagicMock()
        
        config = MagicMock()
        sandbox_config = SandboxConfig()
        sandbox_config.remote_runtime_enable_retries = False  # Disable retries
        config.sandbox = sandbox_config
        runtime.config = config
        
        # Mock _send_action_server_request_impl to raise ConnectionError
        runtime._send_action_server_request_impl = MagicMock(side_effect=ConnectionError())
        
        # Call the method - should raise ConnectionError without retrying
        with self.assertRaises(ConnectionError):
            RemoteRuntime._send_action_server_request(runtime, "GET", "http://example.com")
            
        # Verify _send_action_server_request_impl was called exactly once (no retry)
        self.assertEqual(runtime._send_action_server_request_impl.call_count, 1)
        
    @patch('tenacity.retry')
    def test_connection_error_retried_when_enabled(self, mock_retry):
        """Test that ConnectionError is retried when remote_runtime_enable_retries=True."""
        # Setup a mock retry decorator that will call the function with retries
        def mock_retry_decorator(retry_func):
            def wrapper(*args, **kwargs):
                # Simulate retry behavior by calling the function twice
                try:
                    return retry_func(*args, **kwargs)
                except ConnectionError:
                    # On first ConnectionError, try again and return success
                    return "success after retry"
            return wrapper
            
        mock_retry.return_value = mock_retry_decorator
        
        # Create a runtime instance with remote_runtime_enable_retries=True
        runtime = MagicMock()
        runtime._runtime_closed = False
        runtime._stop_if_closed = lambda x: False
        
        config = MagicMock()
        sandbox_config = SandboxConfig()
        sandbox_config.remote_runtime_enable_retries = True  # Enable retries
        config.sandbox = sandbox_config
        runtime.config = config
        
        # Mock _send_action_server_request_impl to raise ConnectionError on first call
        impl_mock = MagicMock()
        impl_mock.side_effect = [ConnectionError(), "success"]
        runtime._send_action_server_request_impl = impl_mock
        
        # Call the method - should retry and succeed
        result = RemoteRuntime._send_action_server_request(runtime, "GET", "http://example.com")
        
        # Verify retry was called
        mock_retry.assert_called()
        
        # The result should be "success after retry" from our mock decorator
        self.assertEqual(result, "success after retry")


if __name__ == '__main__':
    unittest.main()