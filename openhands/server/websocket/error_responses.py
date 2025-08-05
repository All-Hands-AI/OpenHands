"""
WebSocket Error Response Sys

This module provides standardized error responses for websocket clients
with consistent error codes, messages, and retry information.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union

# Import removed to avoid circular dependency issues
# from openhands.server.websocket.logging import log_websocket_error


class WebSocketErrorCode(Enum):
    """Standardized error codes for websocket operations."""

    # Authentication and Authorization Errors (1000-1099)
    AUTHENTICATION_FAILED = "WS_AUTH_1001"
    INVALID_SESSION_KEY = "WS_AUTH_1002"
    SESSION_EXPIRED = "WS_AUTH_1003"
    AUTHORIZATION_DENIED = "WS_AUTH_1004"

    # Connection Errors (1100-1199)
    CONNECTION_REFUSED = "WS_CONN_1101"
    CONNECTION_TIMEOUT = "WS_CONN_1102"
    CONNECTION_LIMIT_EXCEEDED = "WS_CONN_1103"
    INVALID_CONNECTION_PARAMS = "WS_CONN_1104"

    # Event Processing Errors (1200-1299)
    INVALID_EVENT_FORMAT = "WS_EVENT_1201"
    EVENT_PROCESSING_FAILED = "WS_EVENT_1202"
    UNSUPPORTED_EVENT_TYPE = "WS_EVENT_1203"
    EVENT_VALIDATION_FAILED = "WS_EVENT_1204"

    # Conversation Errors (1300-1399)
    CONVERSATION_NOT_FOUND = "WS_CONV_1301"
    CONVERSATION_ACCESS_DENIED = "WS_CONV_1302"
    CONVERSATION_LOCKED = "WS_CONV_1303"
    INVALID_CONVERSATION_STATE = "WS_CONV_1304"

    # System Errors (1400-1499)
    INTERNAL_SERVER_ERROR = "WS_SYS_1401"
    SERVICE_UNAVAILABLE = "WS_SYS_1402"
    RATE_LIMIT_EXCEEDED = "WS_SYS_1403"
    RESOURCE_EXHAUSTED = "WS_SYS_1404"

    # Client Errors (1500-1599)
    INVALID_REQUEST = "WS_CLIENT_1501"
    MALFORMED_DATA = "WS_CLIENT_1502"
    PROTOCOL_VIOLATION = "WS_CLIENT_1503"
    CLIENT_VERSION_UNSUPPORTED = "WS_CLIENT_1504"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RetryInfo:
    """Information about retry behavior for errors."""

    should_retry: bool
    retry_after_seconds: Optional[float] = None
    max_retries: Optional[int] = None
    backoff_strategy: Optional[str] = None  # "linear", "exponential", "fixed"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"should_retry": self.should_retry}

        if self.retry_after_seconds is not None:
            result["retry_after_seconds"] = self.retry_after_seconds
        if self.max_retries is not None:
            result["max_retries"] = self.max_retries
        if self.backoff_strategy is not None:
            result["backoff_strategy"] = self.backoff_strategy

        return result


@dataclass
class WebSocketErrorResponse:
    """Standardized error response for websocket clients."""

    error_code: WebSocketErrorCode
    message: str
    severity: ErrorSeverity
    timestamp: float
    correlation_id: Optional[str] = None
    retry_info: Optional[RetryInfo] = None
    details: Optional[Dict[str, Any]] = None
    help_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "error_code": self.error_code.value,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
        }

        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.retry_info:
            result["retry_info"] = self.retry_info.to_dict()
        if self.details:
            result["details"] = self.details
        if self.help_url:
            result["help_url"] = self.help_url

        return result


class WebSocketErrorResponseBuilder:
    """Builder for creating standardized error responses."""

    # Default retry configurations for different error types
    DEFAULT_RETRY_CONFIGS = {
        WebSocketErrorCode.CONNECTION_TIMEOUT: RetryInfo(
            should_retry=True,
            retry_after_seconds=2.0,
            max_retries=3,
            backoff_strategy="exponential"
        ),
        WebSocketErrorCode.CONNECTION_LIMIT_EXCEEDED: RetryInfo(
            should_retry=True,
            retry_after_seconds=5.0,
            max_retries=5,
            backoff_strategy="linear"
        ),
        WebSocketErrorCode.RATE_LIMIT_EXCEEDED: RetryInfo(
            should_retry=True,
            retry_after_seconds=10.0,
            max_retries=3,
            backoff_strategy="fixed"
        ),
        WebSocketErrorCode.SERVICE_UNAVAILABLE: RetryInfo(
            should_retry=True,
            retry_after_seconds=30.0,
            max_retries=2,
            backoff_strategy="exponential"
        ),
        WebSocketErrorCode.INTERNAL_SERVER_ERROR: RetryInfo(
            should_retry=True,
            retry_after_seconds=1.0,
            max_retries=2,
            backoff_strategy="exponential"
        ),
        # Authentication errors generally shouldn't be retried
        WebSocketErrorCode.AUTHENTICATION_FAILED: RetryInfo(should_retry=False),
        WebSocketErrorCode.AUTHORIZATION_DENIED: RetryInfo(should_retry=False),
        WebSocketErrorCode.INVALID_SESSION_KEY: RetryInfo(should_retry=False),
        # Client errors shouldn't be retried without fixing the request
        WebSocketErrorCode.INVALID_REQUEST: RetryInfo(should_retry=False),
        WebSocketErrorCode.MALFORMED_DATA: RetryInfo(should_retry=False),
        WebSocketErrorCode.PROTOCOL_VIOLATION: RetryInfo(should_retry=False),
    }

    # Default severity levels for error types
    DEFAULT_SEVERITIES = {
        WebSocketErrorCode.AUTHENTICATION_FAILED: ErrorSeverity.HIGH,
        WebSocketErrorCode.AUTHORIZATION_DENIED: ErrorSeverity.HIGH,
        WebSocketErrorCode.CONNECTION_REFUSED: ErrorSeverity.MEDIUM,
        WebSocketErrorCode.CONNECTION_TIMEOUT: ErrorSeverity.MEDIUM,
        WebSocketErrorCode.INVALID_EVENT_FORMAT: ErrorSeverity.LOW,
        WebSocketErrorCode.CONVERSATION_NOT_FOUND: ErrorSeverity.MEDIUM,
        WebSocketErrorCode.INTERNAL_SERVER_ERROR: ErrorSeverity.CRITICAL,
        WebSocketErrorCode.SERVICE_UNAVAILABLE: ErrorSeverity.HIGH,
        WebSocketErrorCode.RATE_LIMIT_EXCEEDED: ErrorSeverity.MEDIUM,
    }

    # Help URLs for common errors
    HELP_URLS = {
        WebSocketErrorCode.AUTHENTICATION_FAILED: "/docs/troubleshooting/authentication",
        WebSocketErrorCode.CONNECTION_REFUSED: "/docs/troubleshooting/connection-issues",
        WebSocketErrorCode.RATE_LIMIT_EXCEEDED: "/docs/api/rate-limits",
        WebSocketErrorCode.INVALID_EVENT_FORMAT: "/docs/api/websocket-events",
    }

    @classmethod
    def create_error_response(
        cls,
        error_code: WebSocketErrorCode,
        message: str,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        custom_retry_info: Optional[RetryInfo] = None,
        custom_severity: Optional[ErrorSeverity] = None,
        help_url: Optional[str] = None
    ) -> WebSocketErrorResponse:
        """
        Create a standardized error response.

        Args:
            error_code: The error code
            message: Human-readable error message
            correlation_id: Correlation ID for tracking
            details: Additional error details
            custom_retry_info: Custom retry information (overrides default)
            custom_severity: Custom severity (overrides default)
            help_url: Custom help URL (overrides default)

        Returns:
            WebSocketErrorResponse instance
        """
        # Use custom or default retry info
        retry_info = custom_retry_info or cls.DEFAULT_RETRY_CONFIGS.get(error_code)

        # Use custom or default severity
        severity = custom_severity or cls.DEFAULT_SEVERITIES.get(error_code, ErrorSeverity.MEDIUM)

        # Use custom or default help URL
        if help_url is None:
            help_url = cls.HELP_URLS.get(error_code)

        return WebSocketErrorResponse(
            error_code=error_code,
            message=message,
            severity=severity,
            timestamp=time.time(),
            correlation_id=correlation_id,
            retry_info=retry_info,
            details=details,
            help_url=help_url
        )

    @classmethod
    def authentication_failed(
        cls,
        message: str = "Authentication failed",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WebSocketErrorResponse:
        """Create authentication failed error response."""
        return cls.create_error_response(
            WebSocketErrorCode.AUTHENTICATION_FAILED,
            message,
            correlation_id,
            details
        )

    @classmethod
    def connection_refused(
        cls,
        message: str = "Connection refused",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WebSocketErrorResponse:
        """Create connection refused error response."""
        return cls.create_error_response(
            WebSocketErrorCode.CONNECTION_REFUSED,
            message,
            correlation_id,
            details
        )

    @classmethod
    def invalid_event_format(
        cls,
        message: str = "Invalid event format",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WebSocketErrorResponse:
        """Create invalid event format error response."""
        return cls.create_error_response(
            WebSocketErrorCode.INVALID_EVENT_FORMAT,
            message,
            correlation_id,
            details
        )

    @classmethod
    def conversation_not_found(
        cls,
        message: str = "Conversation not found",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WebSocketErrorResponse:
        """Create conversation not found error response."""
        return cls.create_error_response(
            WebSocketErrorCode.CONVERSATION_NOT_FOUND,
            message,
            correlation_id,
            details
        )

    @classmethod
    def internal_server_error(
        cls,
        message: str = "Internal server error",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> WebSocketErrorResponse:
        """Create internal server error response."""
        return cls.create_error_response(
            WebSocketErrorCode.INTERNAL_SERVER_ERROR,
            message,
            correlation_id,
            details
        )

    @classmethod
    def rate_limit_exceeded(
        cls,
        message: str = "Rate limit exceeded",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after_seconds: Optional[float] = None
    ) -> WebSocketErrorResponse:
        """Create rate limit exceeded error response."""
        retry_info = RetryInfo(
            should_retry=True,
            retry_after_seconds=retry_after_seconds or 10.0,
            max_retries=3,
            backoff_strategy="fixed"
        )

        return cls.create_error_response(
            WebSocketErrorCode.RATE_LIMIT_EXCEEDED,
            message,
            correlation_id,
            details,
            custom_retry_info=retry_info
        )


class WebSocketErrorEmitter:
    """Handles emitting error responses to websocket clients."""

    def __init__(self, sio_instance):
        """
        Initialize error emitter.

        Args:
            sio_instance: Socket.IO server instance
        """
        self.sio = sio_instance

    async def emit_error(
        self,
        connection_id: str,
        error_response: WebSocketErrorResponse,
        event_name: str = "oh_error"
    ) -> None:
        """
        Emit error response to a specific client.

        Args:
            connection_id: WebSocket connection ID
            error_response: Error response to emit
            event_name: Socket.IO event name for errors
        """
        try:
            error_data = error_response.to_dict()

            # Log the error emission (simplified logging to avoid circular imports)
            from openhands.core.logger import openhands_logger
            openhands_logger.info(
                f"Emitting error to client: {error_response.error_code.value}",
                extra={
                    "event_type": "error_emission",
                    "connection_id": connection_id,
                    "error_code": error_response.error_code.value,
                    "severity": error_response.severity.value,
                    "correlation_id": error_response.correlation_id
                }
            )

            await self.sio.emit(event_name, error_data, to=connection_id)

        except Exception as e:
            # Log emission failure but don't raise to avoid cascading errors
            from openhands.core.logger import openhands_logger
            openhands_logger.error(
                f"Failed to emit error to client: {str(e)}",
                extra={
                    "event_type": "error_emission_failed",
                    "connection_id": connection_id,
                    "exception": str(e),
                    "type": type(e).__name__,
                    "original_error_code": error_response.error_code.value
                }
            )

    async def emit_error_and_disconnect(
        self,
        connection_id: str,
        error_response: WebSocketErrorResponse,
        event_name: str = "oh_error",
        disconnect_delay_seconds: float = 1.0
    ) -> None:
        """
        Emit error response and then disconnect the client.

        Args:
            connection_id: WebSocket connection ID
            error_response: Error response to emit
            event_name: Socket.IO event name for errors
            disconnect_delay_seconds: Delay before disconnecting to ensure message delivery
        """
        import asyncio

        # Emit the error first
        await self.emit_error(connection_id, error_response, event_name)

        # Wait a bit to ensure the error message is delivered
        if disconnect_delay_seconds > 0:
            await asyncio.sleep(disconnect_delay_seconds)

        # Disconnect the client
        try:
            await self.sio.disconnect(connection_id)

            from openhands.core.logger import openhands_logger
            openhands_logger.info(
                f"Disconnected client after error: {error_response.error_code.value}",
                extra={
                    "event_type": "error_disconnect",
                    "connection_id": connection_id,
                    "error_code": error_response.error_code.value,
                    "disconnect_delay_seconds": disconnect_delay_seconds
                }
            )

        except Exception as e:
            from openhands.core.logger import openhands_logger
            openhands_logger.error(
                f"Failed to disconnect client after error: {str(e)}",
                extra={
                    "event_type": "error_disconnect_failed",
                    "connection_id": connection_id,
                    "exception": str(e),
                    "type": type(e).__name__,
                    "original_error_code": error_response.error_code.value
                }
            )


# Convenience functions for common error scenarios
def create_authentication_error(
    message: str = "Authentication failed",
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> WebSocketErrorResponse:
    """Create authentication error response."""
    return WebSocketErrorResponseBuilder.authentication_failed(message, correlation_id, details)


def create_connection_error(
    message: str = "Connection failed",
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> WebSocketErrorResponse:
    """Create connection error response."""
    return WebSocketErrorResponseBuilder.connection_refused(message, correlation_id, details)


def create_validation_error(
    message: str = "Invalid request format",
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> WebSocketErrorResponse:
    """Create validation error response."""
    return WebSocketErrorResponseBuilder.invalid_event_format(message, correlation_id, details)


def create_server_error(
    message: str = "Internal server error",
    correlation_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> WebSocketErrorResponse:
    """Create server error response."""
    return WebSocketErrorResponseBuilder.internal_server_error(message, correlation_id, details)
