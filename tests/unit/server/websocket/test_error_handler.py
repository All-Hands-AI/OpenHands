"""
Unit tests for WebSocket Error Handler

Tests error classification, response generation, and logging functionality.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from socketio.exceptions import ConnectionRefusedError

from openhands.server.websocket.error_handler import (
    WebSocketErrorHandler,
    WebSocketError,
    ErrorType,
    ErrorCode,
    ErrorSeverity,
    RetryInfo,
Response,
)


class TestWebSocketErrorHandler:
    """Test cases for WebSocketErrorHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = WebSocketErrorHandler()

    def test_classify_connection_refused_error(self):
        """Test classification of ConnectionRefusedError."""
        error = ConnectionRefusedError("No conversation_id in query params")
        result = self.handler.classify_error(error)
        assert result == ErrorType.CONVERSATION_NOT_FOUND

        error = ConnectionRefusedError("Authentication failed")
        result = self.handler.classify_error(error)
        assert result == ErrorType.AUTHENTICATION_FAILED

        error = ConnectionRefusedError("Authorization denied")
        result = self.handler.classify_error(error)
        assert result == ErrorType.AUTHORIZATION_FAILED

        error = ConnectionRefusedError("Generic connection refused")
        result = self.handler.classify_error(error)
        assert result == ErrorType.CONNECTION_REFUSED

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        error = TimeoutError("Connection timeout")
        result = self.handler.classify_error(error)
        assert result == ErrorType.CONNECTION_TIMEOUT

        error = Exception("Request timeout occurred")
        result = self.handler.classify_error(error)
        assert result == ErrorType.CONNECTION_TIMEOUT

    def test_classify_file_not_found_error(self):
        """Test classification of FileNotFoundError."""
        error = FileNotFoundError("Conversation file not found")
        result = self.handler.classify_error(error)
        assert result == ErrorType.CONVERSATION_NOT_FOUND

    def test_classify_serialization_error(self):
        """Test classification of serialization errors."""
        error = json.JSONDecodeError("Invalid JSON", "", 0)
        result = self.handler.classify_error(error)
        assert result == ErrorType.EVENT_SERIALIZATION_FAILED

        error = ValueError("Invalid value format")
        result = self.handler.classify_error(error)
        assert result == ErrorType.INVALID_EVENT_FORMAT

        error = TypeError("Type mismatch")
        result = self.handler.classify_error(error)
        assert result == ErrorType.INVALID_EVENT_FORMAT

    def test_classify_unknown_error(self):
        """Test classification of unknown errors defaults to internal server error."""
        error = RuntimeError("Unknown runtime error")
        result = self.handler.classify_error(error)
        assert result == ErrorType.INTERNAL_SERVER_ERROR

    def test_create_websocket_error(self):
        """Test creation of WebSocketError from generic exception."""
        original_error = ValueError("Invalid input")
        context = {"connection_id": "test_conn_123", "user_id": "user_456"}
        correlation_id = "corr_789"

        ws_error = self.handler.create_websocket_error(
            original_error, context, correlation_id
        )

        assert isinstance(ws_error, WebSocketError)
        assert ws_error.error_type == ErrorType.INVALID_EVENT_FORMAT
        assert ws_error.error_code == ErrorCode.INVALID_EVENT_FORMAT
        assert ws_error.severity == ErrorSeverity.LOW
        assert ws_error.correlation_id == correlation_id
        assert "Connection test_conn_123:" in ws_error.message
        assert ws_error.details["original_error"] == "ValueError"
        assert ws_error.details["connection_id"] == "test_conn_123"
        assert ws_error.retry_info.can_retry is False

    def test_create_websocket_error_with_retry_info(self):
        """Test creation of WebSocketError with retry information."""
        original_error = TimeoutError("Connection timeout")

        ws_error = self.handler.create_websocket_error(original_error)

        assert ws_error.error_type == ErrorType.CONNECTION_TIMEOUT
        assert ws_error.retry_info is not None
        assert ws_error.retry_info.can_retry is True
        assert ws_error.retry_info.retry_after_seconds == 5
        assert ws_error.retry_info.max_retries == 3
        assert ws_error.retry_info.backoff_strategy == "exponential"

    def test_get_retry_info_for_different_error_types(self):
        """Test retry info generation for different error types."""
        # Test retryable error
        retry_info = self.handler._get_retry_info(ErrorType.CONNECTION_LOST)
        assert retry_info.can_retry is True
        assert retry_info.retry_after_seconds == 1
        assert retry_info.max_retries == 5

        # Test non-retryable error
        retry_info = self.handler._get_retry_info(ErrorType.AUTHENTICATION_FAILED)
        assert retry_info.can_retry is False

        # Test rate limit error
        retry_info = self.handler._get_retry_info(ErrorType.RATE_LIMIT_EXCEEDED)
        assert retry_info.can_retry is True
        assert retry_info.retry_after_seconds == 60
        assert retry_info.backoff_strategy == "fixed"

    def test_create_error_response(self):
        """Test creation of standardized error response."""
        ws_error = WebSocketError(
            message="Test error message",
            error_type=ErrorType.CONNECTION_REFUSED,
            error_code=ErrorCode.CONNECTION_REFUSED,
            severity=ErrorSeverity.MEDIUM,
            details={"test_detail": "test_value"},
            retry_info=RetryInfo(can_retry=True, retry_after_seconds=5),
            correlation_id="test_correlation"
        )

        response = self.handler.create_error_response(ws_error)

        assert isinstance(response, ErrorResponse)
        assert response.error_id == ws_error.error_id
        assert response.error_code == ErrorCode.CONNECTION_REFUSED.value
        assert response.error_type == ErrorType.CONNECTION_REFUSED.value
        assert response.message == "Test error message"
        assert response.details == {"test_detail": "test_value"}
        assert response.retry_info.can_retry is True
        assert response.correlation_id == "test_correlation"
        assert isinstance(response.timestamp, datetime)

    @patch('openhands.server.websocket.error_handler.logger')
    def test_log_error_critical_severity(self, mock_logger):
        """Test logging of critical severity errors."""
        ws_error = WebSocketError(
            message="Critical system failure",
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.CRITICAL,
            correlation_id="test_corr"
        )

        self.handler.log_error(ws_error, "conn_123", "user_456")

        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        assert "WebSocket Critical Error:" in call_args[0][0]
        assert call_args[1]['extra']['error_type'] == ErrorType.INTERNAL_SERVER_ERROR.value
        assert call_args[1]['extra']['connection_id'] == "conn_123"
        assert call_args[1]['extra']['user_id'] == "user_456"
        assert call_args[1]['exc_info'] is True

    @patch('openhands.server.websocket.error_handler.logger')
    def test_log_error_high_severity(self, mock_logger):
        """Test logging of high severity errors."""
        ws_error = WebSocketError(
            message="High severity error",
            error_type=ErrorType.DATABASE_ERROR,
            error_code=ErrorCode.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH
        )

        self.handler.log_error(ws_error)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "WebSocket Error:" in call_args[0][0]
        assert call_args[1]['exc_info'] is True

    @patch('openhands.server.websocket.error_handler.logger')
    def test_log_error_medium_severity(self, mock_logger):
        """Test logging of medium severity errors."""
        ws_error = WebSocketError(
            message="Medium severity error",
            error_type=ErrorType.AUTHENTICATION_FAILED,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            severity=ErrorSeverity.MEDIUM
        )

        self.handler.log_error(ws_error)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "WebSocket Warning:" in call_args[0][0]
        # Medium severity doesn't include exc_info
        assert 'exc_info' not in call_args[1]

    @patch('openhands.server.websocket.error_handler.logger')
    def test_log_error_low_severity(self, mock_logger):
        """Test logging of low severity errors."""
        ws_error = WebSocketError(
            message="Low severity error",
            error_type=ErrorType.INVALID_REQUEST,
            error_code=ErrorCode.INVALID_REQUEST,
            severity=ErrorSeverity.LOW
        )

        self.handler.log_error(ws_error)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "WebSocket Info:" in call_args[0][0]

    def test_handle_error_with_exception(self):
        """Test complete error handling flow with generic exception."""
        error = ConnectionRefusedError("Authentication failed")
        context = {"connection_id": "test_conn", "user_id": "test_user"}
        correlation_id = "test_correlation"

        with patch.object(self.handler, 'log_error') as mock_log:
            response = self.handler.handle_error(error, context, correlation_id)

        assert isinstance(response, ErrorResponse)
        assert response.error_type == ErrorType.AUTHENTICATION_FAILED.value
        assert response.error_code == ErrorCode.AUTHENTICATION_FAILED.value
        assert response.correlation_id == correlation_id

        # Verify logging was called
        mock_log.assert_called_once()
        logged_error = mock_log.call_args[0][0]
        assert isinstance(logged_error, WebSocketError)
        assert logged_error.error_type == ErrorType.AUTHENTICATION_FAILED

    def test_handle_error_with_websocket_error(self):
        """Test error handling with pre-created WebSocketError."""
        ws_error = WebSocketError(
            message="Pre-created error",
            error_type=ErrorType.CONNECTION_LOST,
            error_code=ErrorCode.CONNECTION_LOST,
            severity=ErrorSeverity.LOW
        )

        with patch.object(self.handler, 'log_error') as mock_log:
            response = self.handler.handle_error(ws_error)

        assert isinstance(response, ErrorResponse)
        assert response.error_type == ErrorType.CONNECTION_LOST.value

        # Verify the same WebSocketError was logged
        mock_log.assert_called_once()
        logged_error = mock_log.call_args[0][0]
        assert logged_error is ws_error


class TestWebSocketError:
    """Test cases for WebSocketError class."""

    def test_websocket_error_creation(self):
        """Test WebSocketError creation with all parameters."""
        details = {"key": "value"}
        retry_info = RetryInfo(can_retry=True, retry_after_seconds=10)

        error = WebSocketError(
            message="Test error",
            error_type=ErrorType.CONNECTION_TIMEOUT,
            error_code=ErrorCode.CONNECTION_TIMEOUT,
            severity=ErrorSeverity.HIGH,
            details=details,
            retry_info=retry_info,
            correlation_id="test_corr"
        )

        assert error.message == "Test error"
        assert error.error_type == ErrorType.CONNECTION_TIMEOUT
        assert error.error_code == ErrorCode.CONNECTION_TIMEOUT
        assert error.severity == ErrorSeverity.HIGH
        assert error.details == details
        assert error.retry_info == retry_info
        assert error.correlation_id == "test_corr"
        assert error.error_id is not None
        assert isinstance(error.timestamp, datetime)

    def test_websocket_error_defaults(self):
        """Test WebSocketError creation with default values."""
        error = WebSocketError(
            message="Test error",
            error_type=ErrorType.INVALID_REQUEST,
            error_code=ErrorCode.INVALID_REQUEST
        )

        assert error.severity == ErrorSeverity.MEDIUM  # default
        assert error.details == {}  # default empty dict
        assert error.retry_info is None  # default
        assert error.correlation_id is None  # default


class TestRetryInfo:
    """Test cases for RetryInfo model."""

    def test_retry_info_creation(self):
        """Test RetryInfo creation with all parameters."""
        retry_info = RetryInfo(
            can_retry=True,
            retry_after_seconds=30,
            max_retries=5,
            backoff_strategy="exponential"
        )

        assert retry_info.can_retry is True
        assert retry_info.retry_after_seconds == 30
        assert retry_info.max_retries == 5
        assert retry_info.backoff_strategy == "exponential"

    def test_retry_info_minimal(self):
        """Test RetryInfo creation with minimal parameters."""
        retry_info = RetryInfo(can_retry=False)

        assert retry_info.can_retry is False
        assert retry_info.retry_after_seconds is None
        assert retry_info.max_retries is None
        assert retry_info.backoff_strategy is None


class TestErrorResponse:
    """Test cases for ErrorResponse model."""

    def test_error_response_serialization(self):
        """Test ErrorResponse can be serialized to JSON."""
        retry_info = RetryInfo(can_retry=True, retry_after_seconds=5)
        response = ErrorResponse(
            error_id="test_id",
            error_code=1001,
            error_type="connection_refused",
            message="Test message",
            details={"key": "value"},
            retry_info=retry_info,
            timestamp=datetime.utcnow(),
            correlation_id="test_corr"
        )

        # Test that it can be converted to dict (for JSON serialization)
        response_dict = response.model_dump()

        assert response_dict["error_id"] == "test_id"
        assert response_dict["error_code"] == 1001
        assert response_dict["error_type"] == "connection_refused"
        assert response_dict["message"] == "Test message"
        assert response_dict["details"] == {"key": "value"}
        assert response_dict["retry_info"]["can_retry"] is True
        assert response_dict["correlation_id"] == "test_corr"
        assert "timestamp" in response_dict


if __name__ == "__main__":
    pytest.main([__file__])
