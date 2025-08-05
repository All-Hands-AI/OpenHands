"""
Tests for websocket error response system.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.server.websocket.error_responses import (
    ErrorSeverity,
    RetryInfo,
    WebSocketErrorCode,
    WebSocketErrorEmitter,
    WebSocketErrorResponse,
    WebSocketErrorResponseBuilder,
    create_authentication_error,
    create_connection_error,
    create_server_error,
    create_validation_error,
)


class TestRetryInfo:
    """Test cases for RetryInfo class."""

    def test_retry_info_basic(self):
        """Test basic retry info creation."""
        retry_info = RetryInfo(should_retry=True)

        assert retry_info.should_retry is True
        assert retry_info.retry_after_seconds is None
        assert retry_info.max_retries is None
        assert retry_info.backoff_strategy is None

    def test_retry_info_full(self):
        """Test retry info with all fields."""
        retry_info = RetryInfo(
            should_retry=True,
            retry_after_seconds=5.0,
            max_retries=3,
            backoff_strategy="exponential"
        )

        assert retry_info.should_retry is True
        assert retry_info.retry_after_seconds == 5.0
        assert retry_info.max_retries == 3
        assert retry_info.backoff_strategy == "exponential"

    def test_retry_info_to_dict_minimal(self):
        """Test retry info serialization with minimal fields."""
        retry_info = RetryInfo(should_retry=False)
        result = retry_info.to_dict()

        expected = {"should_retry": False}
        assert result == expected

    def test_retry_info_to_dict_full(self):
        """Test retry info serialization with all fields."""
        retry_info = RetryInfo(
            should_retry=True,
            retry_after_seconds=10.0,
            max_retries=5,
            backoff_strategy="linear"
        )
        result = retry_info.to_dict()

        expected = {
            "should_retry": True,
            "retry_after_seconds": 10.0,
            "max_retries": 5,
            "backoff_strategy": "linear"
        }
        assert result == expected


class TestWebSocketErrorResponse:
    """Test cases for WebSocketErrorResponse class."""

    def test_error_response_basic(self):
        """Test basic error response creation."""
        response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.AUTHENTICATION_FAILED,
            message="Authentication failed",
            severity=ErrorSeverity.HIGH,
            timestamp=1234567890.0
        )

        assert response.error_code == WebSocketErrorCode.AUTHENTICATION_FAILED
        assert response.message == "Authentication failed"
        assert response.severity == ErrorSeverity.HIGH
        assert response.timestamp == 1234567890.0
        assert response.correlation_id is None
        assert response.retry_info is None
        assert response.details is None
        assert response.help_url is None

    def test_error_response_full(self):
        """Test error response with all fields."""
        retry_info = RetryInfo(should_retry=True, retry_after_seconds=5.0)
        details = {"reason": "invalid_token"}

        response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.AUTHENTICATION_FAILED,
            message="Authentication failed",
            severity=ErrorSeverity.HIGH,
            timestamp=1234567890.0,
            correlation_id="test-123",
            retry_info=retry_info,
            details=details,
            help_url="/docs/auth"
        )

        assert response.correlation_id == "test-123"
        assert response.retry_info == retry_info
        assert response.details == details
        assert response.help_url == "/docs/auth"

    def test_error_response_to_dict_minimal(self):
        """Test error response serialization with minimal fields."""
        response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.CONNECTION_REFUSED,
            message="Connection refused",
            severity=ErrorSeverity.MEDIUM,
            timestamp=1234567890.0
        )

        result = response.to_dict()
        expected = {
            "error_code": "WS_CONN_1101",
            "message": "Connection refused",
            "severity": "medium",
            "timestamp": 1234567890.0
        }
        assert result == expected

    def test_error_response_to_dict_full(self):
        """Test error response serialization with all fields."""
        retry_info = RetryInfo(should_retry=True, retry_after_seconds=5.0)
        details = {"reason": "timeout"}

        response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.CONNECTION_TIMEOUT,
            message="Connection timed out",
            severity=ErrorSeverity.MEDIUM,
            timestamp=1234567890.0,
            correlation_id="test-456",
            retry_info=retry_info,
            details=details,
            help_url="/docs/connection"
        )

        result = response.to_dict()
        expected = {
            "error_code": "WS_CONN_1102",
            "message": "Connection timed out",
            "severity": "medium",
            "timestamp": 1234567890.0,
            "correlation_id": "test-456",
            "retry_info": {
                "should_retry": True,
                "retry_after_seconds": 5.0
            },
            "details": {"reason": "timeout"},
            "help_url": "/docs/connection"
        }
        assert result == expected


class TestWebSocketErrorResponseBuilder:
    """Test cases for WebSocketErrorResponseBuilder class."""

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_error_response_basic(self, mock_time):
        """Test basic error response creation."""
        mock_time.return_value = 1234567890.0

        response = WebSocketErrorResponseBuilder.create_error_response(
            WebSocketErrorCode.INVALID_REQUEST,
            "Invalid request format"
        )

        assert response.error_code == WebSocketErrorCode.INVALID_REQUEST
        assert response.message == "Invalid request format"
        assert response.severity == ErrorSeverity.MEDIUM  # Default
        assert response.timestamp == 1234567890.0
        assert response.correlation_id is None
        assert response.retry_info is not None  # Should have default
        assert response.retry_info.should_retry is False  # Client errors shouldn't retry

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_error_response_with_defaults(self, mock_time):
        """Test error response creation with default configurations."""
        mock_time.return_value = 1234567890.0

        response = WebSocketErrorResponseBuilder.create_error_response(
            WebSocketErrorCode.CONNECTION_TIMEOUT,
            "Connection timed out"
        )

        assert response.error_code == WebSocketErrorCode.CONNECTION_TIMEOUT
        assert response.severity == ErrorSeverity.MEDIUM
        assert response.retry_info is not None
        assert response.retry_info.should_retry is True
        assert response.retry_info.retry_after_seconds == 2.0
        assert response.retry_info.max_retries == 3
        assert response.retry_info.backoff_strategy == "exponential"

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_error_response_custom_overrides(self, mock_time):
        """Test error response creation with custom overrides."""
        mock_time.return_value = 1234567890.0

        custom_retry = RetryInfo(should_retry=True, retry_after_seconds=10.0)
        custom_severity = ErrorSeverity.CRITICAL
        custom_details = {"custom": "data"}

        response = WebSocketErrorResponseBuilder.create_error_response(
            WebSocketErrorCode.INTERNAL_SERVER_ERROR,
            "Custom server error",
            correlation_id="custom-123",
            details=custom_details,
            custom_retry_info=custom_retry,
            custom_severity=custom_severity,
            help_url="/custom/help"
        )

        assert response.correlation_id == "custom-123"
        assert response.details == custom_details
        assert response.retry_info == custom_retry
        assert response.severity == custom_severity
        assert response.help_url == "/custom/help"

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_authentication_failed_convenience(self, mock_time):
        """Test authentication failed convenience method."""
        mock_time.return_value = 1234567890.0

        response = WebSocketErrorResponseBuilder.authentication_failed(
            "Invalid credentials",
            correlation_id="auth-123",
            details={"reason": "bad_password"}
        )

        assert response.error_code == WebSocketErrorCode.AUTHENTICATION_FAILED
        assert response.message == "Invalid credentials"
        assert response.correlation_id == "auth-123"
        assert response.details == {"reason": "bad_password"}
        assert response.severity == ErrorSeverity.HIGH
        assert response.retry_info.should_retry is False

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_rate_limit_exceeded_with_custom_retry(self, mock_time):
        """Test rate limit exceeded with custom retry time."""
        mock_time.return_value = 1234567890.0

        response = WebSocketErrorResponseBuilder.rate_limit_exceeded(
            "Too many requests",
            retry_after_seconds=30.0
        )

        assert response.error_code == WebSocketErrorCode.RATE_LIMIT_EXCEEDED
        assert response.retry_info.should_retry is True
        assert response.retry_info.retry_after_seconds == 30.0
        assert response.retry_info.max_retries == 3
        assert response.retry_info.backoff_strategy == "fixed"

    def test_default_configurations_coverage(self):
        """Test that default configurations cover important error codes."""
        # Check that critical error codes have retry configurations
        critical_codes = [
            WebSocketErrorCode.CONNECTION_TIMEOUT,
            WebSocketErrorCode.CONNECTION_LIMIT_EXCEEDED,
            WebSocketErrorCode.RATE_LIMIT_EXCEEDED,
            WebSocketErrorCode.SERVICE_UNAVAILABLE,
            WebSocketErrorCode.INTERNAL_SERVER_ERROR
        ]

        for code in critical_codes:
            assert code in WebSocketErrorResponseBuilder.DEFAULT_RETRY_CONFIGS
            retry_config = WebSocketErrorResponseBuilder.DEFAULT_RETRY_CONFIGS[code]
            assert isinstance(retry_config, RetryInfo)

        # Check that authentication errors are configured not to retry
        auth_codes = [
            WebSocketErrorCode.AUTHENTICATION_FAILED,
            WebSocketErrorCode.AUTHORIZATION_DENIED,
            WebSocketErrorCode.INVALID_SESSION_KEY
        ]

        for code in auth_codes:
            if code in WebSocketErrorResponseBuilder.DEFAULT_RETRY_CONFIGS:
                retry_config = WebSocketErrorResponseBuilder.DEFAULT_RETRY_CONFIGS[code]
                assert retry_config.should_retry is False


class TestWebSocketErrorEmitter:
    """Test cases for WebSocketErrorEmitter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sio = AsyncMock()
        self.emitter = WebSocketErrorEmitter(self.mock_sio)

    @patch('openhands.server.websocket.error_responses.log_websocket_error')
    async def test_emit_error_success(self, mock_log):
        """Test successful error emission."""
        error_response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.AUTHENTICATION_FAILED,
            message="Auth failed",
            severity=ErrorSeverity.HIGH,
            timestamp=1234567890.0,
            correlation_id="test-123"
        )

        await self.emitter.emit_error("conn_123", error_response)

        # Verify socket emission
        self.mock_sio.emit.assert_called_once_with(
            "oh_error",
            error_response.to_dict(),
            to="conn_123"
        )

        # Verify logging
        mock_log.assert_called_once()
        args, kwargs = mock_log.call_args
        assert kwargs["error_type"] == "error_emission"
        assert kwargs["connection_id"] == "conn_123"

    @patch('openhands.server.websocket.error_responses.log_websocket_error')
    async def test_emit_error_custom_event_name(self, mock_log):
        """Test error emission with custom event name."""
        error_response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.CONNECTION_REFUSED,
            message="Connection refused",
            severity=ErrorSeverity.MEDIUM,
            timestamp=1234567890.0
        )

        await self.emitter.emit_error("conn_456", error_response, "custom_error")

        self.mock_sio.emit.assert_called_once_with(
            "custom_error",
            error_response.to_dict(),
            to="conn_456"
        )

    @patch('openhands.server.websocket.error_responses.log_websocket_error')
    async def test_emit_error_failure_handling(self, mock_log):
        """Test error emission failure handling."""
        error_response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.INTERNAL_SERVER_ERROR,
            message="Server error",
            severity=ErrorSeverity.CRITICAL,
            timestamp=1234567890.0
        )

        # Make socket emission fail
        self.mock_sio.emit.side_effect = Exception("Socket error")

        # Should not raise exception
        await self.emitter.emit_error("conn_789", error_response)

        # Should log the emission failure
        assert mock_log.call_count == 2  # One for attempt, one for failure
        failure_call = mock_log.call_args_list[1]
        assert failure_call[1]["error_type"] == "error_emission_failed"

    @patch('openhands.server.websocket.error_responses.log_websocket_error')
    async def test_emit_error_and_disconnect(self, mock_log):
        """Test error emission followed by disconnection."""
        error_response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.PROTOCOL_VIOLATION,
            message="Protocol violation",
            severity=ErrorSeverity.HIGH,
            timestamp=1234567890.0
        )

        with patch('asyncio.sleep') as mock_sleep:
            await self.emitter.emit_error_and_disconnect(
                "conn_disconnect",
                error_response,
                disconnect_delay_seconds=0.5
            )

        # Verify emission
        self.mock_sio.emit.assert_called_once()

        # Verify delay
        mock_sleep.assert_called_once_with(0.5)

        # Verify disconnection
        self.mock_sio.disconnect.assert_called_once_with("conn_disconnect")

        # Verify logging (emission + disconnection)
        assert mock_log.call_count == 2

    @patch('openhands.server.websocket.error_responses.log_websocket_error')
    async def test_emit_error_and_disconnect_no_delay(self, mock_log):
        """Test error emission and disconnection with no delay."""
        error_response = WebSocketErrorResponse(
            error_code=WebSocketErrorCode.CLIENT_VERSION_UNSUPPORTED,
            message="Unsupported client",
            severity=ErrorSeverity.MEDIUM,
            timestamp=1234567890.0
        )

        with patch('asyncio.sleep') as mock_sleep:
            await self.emitter.emit_error_and_disconnect(
                "conn_nodelay",
                error_response,
                disconnect_delay_seconds=0.0
            )

        # Should not sleep when delay is 0
        mock_sleep.assert_not_called()

        # Should still disconnect
        self.mock_sio.disconnect.assert_called_once_with("conn_nodelay")


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_authentication_error(self, mock_time):
        """Test authentication error convenience function."""
        mock_time.return_value = 1234567890.0

        response = create_authentication_error(
            "Invalid token",
            correlation_id="auth-test",
            details={"token_type": "bearer"}
        )

        assert response.error_code == WebSocketErrorCode.AUTHENTICATION_FAILED
        assert response.message == "Invalid token"
        assert response.correlation_id == "auth-test"
        assert response.details == {"token_type": "bearer"}

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_connection_error(self, mock_time):
        """Test connection error convenience function."""
        mock_time.return_value = 1234567890.0

        response = create_connection_error(
            "Connection timeout",
            correlation_id="conn-test"
        )

        assert response.error_code == WebSocketErrorCode.CONNECTION_REFUSED
        assert response.message == "Connection timeout"
        assert response.correlation_id == "conn-test"

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_validation_error(self, mock_time):
        """Test validation error convenience function."""
        mock_time.return_value = 1234567890.0

        response = create_validation_error(
            "Missing required field",
            details={"field": "conversation_id"}
        )

        assert response.error_code == WebSocketErrorCode.INVALID_EVENT_FORMAT
        assert response.message == "Missing required field"
        assert response.details == {"field": "conversation_id"}

    @patch('openhands.server.websocket.error_responses.time.time')
    def test_create_server_error(self, mock_time):
        """Test server error convenience function."""
        mock_time.return_value = 1234567890.0

        response = create_server_error(
            "Database connection failed",
            correlation_id="server-test",
            details={"service": "postgresql"}
        )

        assert response.error_code == WebSocketErrorCode.INTERNAL_SERVER_ERROR
        assert response.message == "Database connection failed"
        assert response.correlation_id == "server-test"
        assert response.details == {"service": "postgresql"}


class TestErrorCodeValues:
    """Test that error codes have expected values."""

    def test_error_code_format(self):
        """Test that error codes follow the expected format."""
        for error_code in WebSocketErrorCode:
            value = error_code.value
            assert value.startswith("WS_")
            assert "_" in value
            # Should end with a 4-digit number
            assert value[-4:].isdigit()

    def test_error_code_uniqueness(self):
        """Test that all error codes are unique."""
        values = [code.value for code in WebSocketErrorCode]
        assert len(values) == len(set(values))

    def test_error_code_categories(self):
        """Test that error codes are properly categorized by number ranges."""
        auth_codes = [code for code in WebSocketErrorCode if "AUTH" in code.name]
        conn_codes = [code for code in WebSocketErrorCode if "CONN" in code.name]
        event_codes = [code for code in WebSocketErrorCode if "EVENT" in code.name]
        conv_codes = [code for code in WebSocketErrorCode if "CONV" in code.name]
        sys_codes = [code for code in WebSocketErrorCode if "SYS" in code.name]
        client_codes = [code for code in WebSocketErrorCode if "CLIENT" in code.name]

        # Check that codes are in expected ranges
        for code in auth_codes:
            assert "1001" <= code.value[-4:] <= "1099"

        for code in conn_codes:
            assert "1101" <= code.value[-4:] <= "1199"

        for code in event_codes:
            assert "1201" <= code.value[-4:] <= "1299"

        for code in conv_codes:
            assert "1301" <= code.value[-4:] <= "1399"

        for code in sys_codes:
            assert "1401" <= code.value[-4:] <= "1499"

        for code in client_codes:
            assert "1501" <= code.value[-4:] <= "1599"
