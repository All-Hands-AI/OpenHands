"""
WebSocket Error Handling System

This module provides comprehensive error classification, handling, and response
generation for websocket connections in the OpenHands application.
"""

import traceback
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger


class ErrorType(Enum):
    """Classification of websocket error types."""

    # Connection Errors
    CONNECTION_REFUSED = "connection_refused"
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_LIMIT_EXCEEDED = "connection_limit_exceeded"

    # Authentication/Authorization Errors
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_FAILED = "authorization_failed"
    SESSION_EXPIRED = "session_expired"
    INVALID_CREDENTIALS = "invalid_credentials"

    # Event Processing Errors
    INVALID_EVENT_FORMAT = "invalid_event_format"
    EVENT_PROCESSING_FAILED = "event_processing_failed"
    EVENT_SERIALIZATION_FAILED = "event_serialization_failed"
    CONVERSATION_NOT_FOUND = "conversation_not_found"

    # System Errors
    INTERNAL_SERVER_ERROR = "internal_server_error"
    DATABASE_ERROR = "database_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    SERVICE_UNAVAILABLE = "service_unavailable"

    # Client Errors
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PROTOCOL_VIOLATION = "protocol_violation"
    MALFORMED_DATA = "malformed_data"


class ErrorSeverity(Enum):
    """Error severity levels for monitoring and alerting."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCode(Enum):
    """Standardized error codes for client communication."""

    # 1000-1999: Connection errors
    CONNECTION_REFUSED = 1001
    CONNECTION_TIMEOUT = 1002
    CONNECTION_LOST = 1003
    CONNECTION_LIMIT_EXCEEDED = 1004

    # 2000-2999: Authentication/Authorization errors
    AUTHENTICATION_FAILED = 2001
    AUTHORIZATION_FAILED = 2002
    SESSION_EXPIRED = 2003
    INVALID_CREDENTIALS = 2004

    # 3000-3999: Event processing errors
    INVALID_EVENT_FORMAT = 3001
    EVENT_PROCESSING_FAILED = 3002
    EVENT_SERIALIZATION_FAILED = 3003
    CONVERSATION_NOT_FOUND = 3004

    # 4000-4999: System errors
    INTERNAL_SERVER_ERROR = 4001
    DATABASE_ERROR = 4002
    RESOURCE_EXHAUSTED = 4003
    SERVICE_UNAVAILABLE = 4004

    # 5000-5999: Client errors
    INVALID_REQUEST = 5001
    RATE_LIMIT_EXCEEDED = 5002
    PROTOCOL_VIOLATION = 5003
    MALFORMED_DATA = 5004


class RetryInfo(BaseModel):
    """Information about retry behavior for recoverable errors."""

    can_retry: bool
    retry_after_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    backoff_strategy: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response structure for client communication."""

    error_id: str
    error_code: int
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_info: Optional[RetryInfo] = None
    timestamp: datetime
    correlation_id: Optional[str] = None


class WebSocketError(Exception):
    """Base exception class for websocket-specific errors."""

    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        error_code: ErrorCode,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        retry_info: Optional[RetryInfo] = None,
        correlation_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.retry_info = retry_info
        self.correlation_id = correlation_id
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()


class WebSocketErrorHandler:
    """Handles websocket error classification, logging, and response generation."""

    # Error type to severity mapping
    ERROR_SEVERITY_MAP = {
        ErrorType.CONNECTION_REFUSED: ErrorSeverity.MEDIUM,
        ErrorType.CONNECTION_TIMEOUT: ErrorSeverity.MEDIUM,
        ErrorType.CONNECTION_LOST: ErrorSeverity.LOW,
        ErrorType.CONNECTION_LIMIT_EXCEEDED: ErrorSeverity.HIGH,

        ErrorType.AUTHENTICATION_FAILED: ErrorSeverity.MEDIUM,
        ErrorType.AUTHORIZATION_FAILED: ErrorSeverity.MEDIUM,
        ErrorType.SESSION_EXPIRED: ErrorSeverity.LOW,
        ErrorType.INVALID_CREDENTIALS: ErrorSeverity.MEDIUM,

        ErrorType.INVALID_EVENT_FORMAT: ErrorSeverity.LOW,
        ErrorType.EVENT_PROCESSING_FAILED: ErrorSeverity.MEDIUM,
        ErrorType.EVENT_SERIALIZATION_FAILED: ErrorSeverity.MEDIUM,
        ErrorType.CONVERSATION_NOT_FOUND: ErrorSeverity.MEDIUM,

        ErrorType.INTERNAL_SERVER_ERROR: ErrorSeverity.CRITICAL,
        ErrorType.DATABASE_ERROR: ErrorSeverity.HIGH,
        ErrorType.RESOURCE_EXHAUSTED: ErrorSeverity.HIGH,
        ErrorType.SERVICE_UNAVAILABLE: ErrorSeverity.CRITICAL,

        ErrorType.INVALID_REQUEST: ErrorSeverity.LOW,
        ErrorType.RATE_LIMIT_EXCEEDED: ErrorSeverity.MEDIUM,
        ErrorType.PROTOCOL_VIOLATION: ErrorSeverity.MEDIUM,
        ErrorType.MALFORMED_DATA: ErrorSeverity.LOW,
    }

    # Error type to code mapping
    ERROR_CODE_MAP = {
        ErrorType.CONNECTION_REFUSED: ErrorCode.CONNECTION_REFUSED,
        ErrorType.CONNECTION_TIMEOUT: ErrorCode.CONNECTION_TIMEOUT,
        ErrorType.CONNECTION_LOST: ErrorCode.CONNECTION_LOST,
        ErrorType.CONNECTION_LIMIT_EXCEEDED: ErrorCode.CONNECTION_LIMIT_EXCEEDED,

        ErrorType.AUTHENTICATION_FAILED: ErrorCode.AUTHENTICATION_FAILED,
        ErrorType.AUTHORIZATION_FAILED: ErrorCode.AUTHORIZATION_FAILED,
        ErrorType.SESSION_EXPIRED: ErrorCode.SESSION_EXPIRED,
        ErrorType.INVALID_CREDENTIALS: ErrorCode.INVALID_CREDENTIALS,

        ErrorType.INVALID_EVENT_FORMAT: ErrorCode.INVALID_EVENT_FORMAT,
        ErrorType.EVENT_PROCESSING_FAILED: ErrorCode.EVENT_PROCESSING_FAILED,
        ErrorType.EVENT_SERIALIZATION_FAILED: ErrorCode.EVENT_SERIALIZATION_FAILED,
        ErrorType.CONVERSATION_NOT_FOUND: ErrorCode.CONVERSATION_NOT_FOUND,

        ErrorType.INTERNAL_SERVER_ERROR: ErrorCode.INTERNAL_SERVER_ERROR,
        ErrorType.DATABASE_ERROR: ErrorCode.DATABASE_ERROR,
        ErrorType.RESOURCE_EXHAUSTED: ErrorCode.RESOURCE_EXHAUSTED,
        ErrorType.SERVICE_UNAVAILABLE: ErrorCode.SERVICE_UNAVAILABLE,

        ErrorType.INVALID_REQUEST: ErrorCode.INVALID_REQUEST,
        ErrorType.RATE_LIMIT_EXCEEDED: ErrorCode.RATE_LIMIT_EXCEEDED,
        ErrorType.PROTOCOL_VIOLATION: ErrorCode.PROTOCOL_VIOLATION,
        ErrorType.MALFORMED_DATA: ErrorCode.MALFORMED_DATA,
    }

    def __init__(self):
        self.logger = logger

    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorType:
        """
        Classify an exception into a websocket error type.

        Args:
            error: The exception to classify
            context: Additional context about the error

        Returns:
            The classified error type
        """
        context = context or {}
        error_name = error.__class__.__name__
        error_message = str(error).lower()

        # Connection-related errors
        if "connectionrefusederror" in error_name.lower():
            if "conversation_id" in error_message:
                return ErrorType.CONVERSATION_NOT_FOUND
            elif "authentication" in error_message or "auth" in error_message:
                return ErrorType.AUTHENTICATION_FAILED
            elif "authorization" in error_message:
                return ErrorType.AUTHORIZATION_FAILED
            else:
                return ErrorType.CONNECTION_REFUSED

        if "timeout" in error_name.lower() or "timeout" in error_message:
            return ErrorType.CONNECTION_TIMEOUT

        if "connectionerror" in error_name.lower() or "disconnect" in error_message:
            return ErrorType.CONNECTION_LOST

        # File/Database errors
        if "filenotfounderror" in error_name.lower():
            return ErrorType.CONVERSATION_NOT_FOUND

        if any(db_error in error_name.lower() for db_error in ["database", "sql", "redis"]):
            return ErrorType.DATABASE_ERROR

        # Serialization/Format errors
        if any(format_error in error_name.lower() for format_error in ["json", "serialization", "decode"]):
            return ErrorType.EVENT_SERIALIZATION_FAILED

        if "valueerror" in error_name.lower() or "typeerror" in error_name.lower():
            return ErrorType.INVALID_EVENT_FORMAT

        # Permission/Auth errors
        if any(auth_error in error_name.lower() for auth_error in ["permission", "forbidden", "unauthorized"]):
            return ErrorType.AUTHORIZATION_FAILED

        # Resource errors
        if any(resource_error in error_name.lower() for resource_error in ["memory", "resource", "limit"]):
            return ErrorType.RESOURCE_EXHAUSTED

        # Default to internal server error for unclassified exceptions
        return ErrorType.INTERNAL_SERVER_ERROR

    def create_websocket_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> WebSocketError:
        """
        Create a WebSocketError from a generic exception.

        Args:
            error: The original exception
            context: Additional context about the error
            correlation_id: Correlation ID for tracking

        Returns:
            A WebSocketError instance
        """
        error_type = self.classify_error(error, context)
        error_code = self.ERROR_CODE_MAP[error_type]
        severity = self.ERROR_SEVERITY_MAP[error_type]

        # Create retry info for recoverable errors
        retry_info = self._get_retry_info(error_type)

        # Enhance error message with context
        message = str(error)
        if context and context.get("connection_id"):
            message = f"Connection {context['connection_id']}: {message}"

        details = {
            "original_error": error.__class__.__name__,
            "original_message": str(error),
        }
        if context:
            details.update(context)

        return WebSocketError(
            message=message,
            error_type=error_type,
            error_code=error_code,
            severity=severity,
            details=details,
            retry_info=retry_info,
            correlation_id=correlation_id,
        )

    def _get_retry_info(self, error_type: ErrorType) -> Optional[RetryInfo]:
        """Get retry information for an error type."""

        # Errors that can be retried
        retryable_errors = {
            ErrorType.CONNECTION_TIMEOUT: RetryInfo(
                can_retry=True,
                retry_after_seconds=5,
                max_retries=3,
                backoff_strategy="exponential"
            ),
            ErrorType.CONNECTION_LOST: RetryInfo(
                can_retry=True,
                retry_after_seconds=1,
                max_retries=5,
                backoff_strategy="exponential"
            ),
            ErrorType.DATABASE_ERROR: RetryInfo(
                can_retry=True,
                retry_after_seconds=10,
                max_retries=2,
                backoff_strategy="linear"
            ),
            ErrorType.SERVICE_UNAVAILABLE: RetryInfo(
                can_retry=True,
                retry_after_seconds=30,
                max_retries=3,
                backoff_strategy="exponential"
            ),
            ErrorType.RATE_LIMIT_EXCEEDED: RetryInfo(
                can_retry=True,
                retry_after_seconds=60,
                max_retries=1,
                backoff_strategy="fixed"
            ),
        }

        return retryable_errors.get(error_type, RetryInfo(can_retry=False))

    def create_error_response(self, ws_error: WebSocketError) -> ErrorResponse:
        """
        Create a standardized error response for client communication.

        Args:
            ws_error: The WebSocketError to convert

        Returns:
            An ErrorResponse for the client
        """
        return ErrorResponse(
            error_id=ws_error.error_id,
            error_code=ws_error.error_code.value,
            error_type=ws_error.error_type.value,
            message=ws_error.message,
            details=ws_error.details,
            retry_info=ws_error.retry_info,
            timestamp=ws_error.timestamp,
            correlation_id=ws_error.correlation_id,
        )

    def log_error(
        self,
        ws_error: WebSocketError,
        connection_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Log a websocket error with appropriate level and context.

        Args:
            ws_error: The WebSocketError to log
            connection_id: Connection ID if available
            user_id: User ID if available
        """
        log_context = {
            "error_id": ws_error.error_id,
            "error_type": ws_error.error_type.value,
            "error_code": ws_error.error_code.value,
            "severity": ws_error.severity.value,
            "correlation_id": ws_error.correlation_id,
            "connection_id": connection_id,
            "user_id": user_id,
        }

        # Add details to log context
        if ws_error.details:
            log_context.update(ws_error.details)

        # Log at appropriate level based on severity
        if ws_error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"WebSocket Critical Error: {ws_error.message}",
                extra=log_context,
                exc_info=True
            )
        elif ws_error.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"WebSocket Error: {ws_error.message}",
                extra=log_context,
                exc_info=True
            )
        elif ws_error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"WebSocket Warning: {ws_error.message}",
                extra=log_context
            )
        else:  # LOW severity
            self.logger.info(
                f"WebSocket Info: {ws_error.message}",
                extra=log_context
            )

    def handle_error(
        self,
        error: Union[Exception, WebSocketError],
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> ErrorResponse:
        """
        Handle an error by classifying, logging, and creating a response.

        Args:
            error: The error to handle
            context: Additional context
            correlation_id: Correlation ID for tracking

        Returns:
            An ErrorResponse for the client
        """
        # Convert to WebSocketError if needed
        if isinstance(error, WebSocketError):
            ws_error = error
        else:
            ws_error = self.create_websocket_error(error, context, correlation_id)

        # Log the error
        connection_id = context.get("connection_id") if context else None
        user_id = context.get("user_id") if context else None
        self.log_error(ws_error, connection_id, user_id)

        # Create and return error response
        return self.create_error_response(ws_error)
