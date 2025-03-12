"""Test the retry decorator functionality."""

import unittest
from unittest.mock import MagicMock, patch

import requests
import tenacity
from requests.exceptions import ConnectionError, HTTPError

from openhands.runtime.utils.request import is_retryable_error, send_request


class TestRetryDecorator(unittest.TestCase):
    """Test the retry decorator functionality."""

    def test_is_retryable_error(self):
        """Test that is_retryable_error correctly identifies retryable errors."""
        # 429 errors should be retryable
        mock_response = MagicMock()
        mock_response.status_code = 429
        http_error = HTTPError(response=mock_response)
        self.assertTrue(is_retryable_error(http_error))
        
        # ConnectionError should be retryable
        conn_error = ConnectionError()
        self.assertTrue(is_retryable_error(conn_error))
        
        # Other HTTP errors should not be retryable
        mock_response.status_code = 404
        http_error = HTTPError(response=mock_response)
        self.assertFalse(is_retryable_error(http_error))
        
        # Other exceptions should not be retryable
        value_error = ValueError()
        self.assertFalse(is_retryable_error(value_error))

    @patch('openhands.runtime.utils.request.HttpSession')
    def test_send_request_retries_on_connection_error(self, mock_session_class):
        """Test that send_request retries on ConnectionError."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock request to raise ConnectionError on first call, then succeed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.request.side_effect = [ConnectionError(), mock_response]
        
        # Call send_request
        result = send_request(mock_session, "GET", "http://example.com")
        
        # Verify that request was called twice (retry happened)
        self.assertEqual(mock_session.request.call_count, 2)
        self.assertEqual(result, mock_response)

    @patch('openhands.runtime.utils.request.HttpSession')
    def test_send_request_retries_on_429(self, mock_session_class):
        """Test that send_request retries on 429 Too Many Requests."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Create a 429 response for the first call
        error_response = MagicMock()
        error_response.status_code = 429
        error_response.raise_for_status.side_effect = HTTPError(response=error_response)
        
        # Create a successful response for the second call
        success_response = MagicMock()
        success_response.status_code = 200
        
        # Mock request to return 429 on first call, then succeed
        mock_session.request.side_effect = [error_response, success_response]
        
        # Call send_request
        result = send_request(mock_session, "GET", "http://example.com")
        
        # Verify that request was called twice (retry happened)
        self.assertEqual(mock_session.request.call_count, 2)
        self.assertEqual(result, success_response)


if __name__ == '__main__':
    unittest.main()