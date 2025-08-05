"""
Tests for websocket structured logging system.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from openhands.server.websocket.logging import (
    CorrelationIdManager,
    WebSocketLogger,
    log_websocket_connection,
    log_websocket_error,
    log_websocket_event,
    log_websocket_metrics,
    websocket_logger,
)


class TestWebSocketLogger:
    """Test cases for WebSocketLogger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = WebSocketLogger("test_websocket")

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_log_connection_event_basic(self, mock_logger):
        """Test basic connection event logging."""
r.log_connection_event(
            event_type="connect",
            message="User connected",
            connection_id="conn_123",
            user_id="user_456",
            conversation_id="conv_789"
        )

        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args

        assert args[0] == "User connected"
        assert "extra" in kwargs

        extra = kwargs["extra"]
        assert extra["logger_name"] == "test_websocket"
        assert extra["event_type"] == "connection_connect"
        assert extra["connection_id"] == "conn_123"
        assert extra["user_id"] == "user_456"
        assert extra["conversation_id"] == "conv_789"
        assert "timestamp" in extra
        assert "correlation_id" in extra

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_log_connection_event_with_correlation_id(self, mock_logger):
        """Test connection event logging with correlation ID."""
        correlation_id = "test-correlation-123"

        with CorrelationIdManager.correlation_context(correlation_id):
            self.logger.log_connection_event(
                event_type="disconnect",
                message="User disconnected",
                connection_id="conn_123"
            )

        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args

        extra = kwargs["extra"]
        assert extra["correlation_id"] == correlation_id

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_log_event_processing_with_data(self, mock_logger):
        """Test event processing logging with event data."""
        event_data = {
            "action": "send_message",
            "content": "Hello world",
            "password": "secret123",  # Should be sanitized
            "metadata": {
                "token": "abc123",  # Should be sanitized
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }

        self.logger.log_event_processing(
            event_type="message",
            message="Processing message event",
            connection_id="conn_123",
            event_data=event_data,
            processing_time_ms=150.5
        )

        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args

        extra = kwargs["extra"]
        assert extra["event_type"] == "event_message"
        assert extra["processing_time_ms"] == 150.5

        # Check that sensitive data was sanitized
        sanitized_data = extra["event_data"]
        assert sanitized_data["password"] == "[REDACTED]"
        assert sanitized_data["metadata"]["token"] == "[REDACTED]"
        assert sanitized_data["content"] == "Hello world"  # Non-sensitive data preserved
        assert sanitized_data["metadata"]["timestamp"] == "2023-01-01T00:00:00Z"

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_log_error_with_details(self, mock_logger):
        """Test error logging with error details."""
        error_details = {
            "error_code": "CONN_TIMEOUT",
            "retry_count": 3,
            "last_attempt": "2023-01-01T00:00:00Z"
        }

        self.logger.log_error(
            error_type="connection_timeout",
            message="Connection timed out after 3 retries",
            connection_id="conn_123",
            error_details=error_details
        )

        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args

        extra = kwargs["extra"]
        assert extra["event_type"] == "error_connection_timeout"
        assert extra["error_details"] == error_details

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_log_metrics(self, mock_logger):
        """Test metrics logging."""
        metrics = {
            "active_connections": 42,
            "messages_per_second": 15.7,
            "average_latency_ms": 125.3
        }

        self.logger.log_metrics(
            metric_type="performance",
            message="Connection performance metrics",
            metrics=metrics
        )

        mock_logger.info.assert_called_once()
        args, kwargs = mock_logger.info.call_args

        extra = kwargs["extra"]
        assert extra["event_type"] == "metrics_performance"
        assert extra["metrics"] == metrics

    def test_sanitize_event_data_nested(self):
        """Test event data sanitization with nested structures."""
        event_data = {
            "user": {
                "name": "John Doe",
                "password": "secret123",
                "profile": {
                    "email": "john@example.com",
                    "api_key": "key123"
                }
            },
            "messages": [
                {"content": "Hello", "token": "abc123"},
                {"content": "World", "auth": "xyz789"}
            ],
            "normal_field": "normal_value"
        }

        sanitized = self.logger._sanitize_event_data(event_data)

        assert sanitized["user"]["name"] == "John Doe"
        assert sanitized["user"]["password"] == "[REDACTED]"
        assert sanitized["user"]["profile"]["email"] == "john@example.com"
        assert sanitized["user"]["profile"]["api_key"] == "[REDACTED]"
        assert sanitized["messages"][0]["content"] == "Hello"
        assert sanitized["messages"][0]["token"] == "[REDACTED]"
        assert sanitized["messages"][1]["content"] == "World"
        assert sanitized["messages"][1]["auth"] == "[REDACTED]"
        assert sanitized["normal_field"] == "normal_value"

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_different_log_levels(self, mock_logger):
        """Test logging with different log levels."""
        # Test debug level
        self.logger.log_connection_event(
            event_type="heartbeat",
            message="Heartbeat received",
            level="debug"
        )
        mock_logger.debug.assert_called_once()

        # Test warning level
        self.logger.log_connection_event(
            event_type="slow_response",
            message="Slow response detected",
            level="warning"
        )
        mock_logger.warning.assert_called_once()

        # Test error level
        self.logger.log_error(
            error_type="validation",
            message="Validation failed",
            level="critical"
        )
        mock_logger.critical.assert_called_once()


class TestCorrelationIdManager:
    """Test cases for CorrelationIdManager."""

    def test_generate_correlation_id(self):
        """Test correlation ID generation."""
        correlation_id = CorrelationIdManager.generate_correlation_id()

        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
        # Should be a valid UUID format
        uuid.UUID(correlation_id)

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = "test-correlation-123"

        CorrelationIdManager.set_correlation_id(test_id)
        retrieved_id = CorrelationIdManager.get_correlation_id()

        assert retrieved_id == test_id

    def test_correlation_context_manager(self):
        """Test correlation ID context manager."""
        test_id = "context-test-456"

        # Test with provided correlation ID
        with CorrelationIdManager.correlation_context(test_id) as context_id:
            assert context_id == test_id
            assert CorrelationIdManager.get_correlation_id() == test_id

        # Context should be cleared after exiting
        assert CorrelationIdManager.get_correlation_id() is None

    def test_correlation_context_manager_auto_generate(self):
        """Test correlation ID context manager with auto-generation."""
        with CorrelationIdManager.correlation_context() as context_id:
            assert context_id is not None
            assert isinstance(context_id, str)
            assert CorrelationIdManager.get_correlation_id() == context_id
            # Should be a valid UUID
            uuid.UUID(context_id)

        # Context should be cleared after exiting
        assert CorrelationIdManager.get_correlation_id() is None

    def test_nested_correlation_contexts(self):
        """Test nested correlation ID contexts."""
        outer_id = "outer-123"
        inner_id = "inner-456"

        with CorrelationIdManager.correlation_context(outer_id):
            assert CorrelationIdManager.get_correlation_id() == outer_id

            with CorrelationIdManager.correlation_context(inner_id):
                assert CorrelationIdManager.get_correlation_id() == inner_id

            # Should restore outer context
            assert CorrelationIdManager.get_correlation_id() == outer_id

        # Should be cleared completely
        assert CorrelationIdManager.get_correlation_id() is None


class TestConvenienceFunctions:
    """Test cases for convenience logging functions."""

    @patch('openhands.server.websocket.logging.websocket_logger')
    def test_log_websocket_connection(self, mock_logger):
        """Test log_websocket_connection convenience function."""
        log_websocket_connection(
            event_type="connect",
            message="User connected",
            connection_id="conn_123",
            user_id="user_456"
        )

        mock_logger.log_connection_event.assert_called_once_with(
            event_type="connect",
            message="User connected",
            connection_id="conn_123",
            user_id="user_456",
            conversation_id=None,
            level="info"
        )

    @patch('openhands.server.websocket.logging.websocket_logger')
    def test_log_websocket_event(self, mock_logger):
        """Test log_websocket_event convenience function."""
        event_data = {"action": "test"}

        log_websocket_event(
            event_type="message",
            message="Processing message",
            connection_id="conn_123",
            event_data=event_data,
            processing_time_ms=100.0
        )

        mock_logger.log_event_processing.assert_called_once_with(
            event_type="message",
            message="Processing message",
            connection_id="conn_123",
            user_id=None,
            conversation_id=None,
            event_data=event_data,
            processing_time_ms=100.0,
            level="info"
        )

    @patch('openhands.server.websocket.logging.websocket_logger')
    def test_log_websocket_error(self, mock_logger):
        """Test log_websocket_error convenience function."""
        error_details = {"code": "TIMEOUT"}

        log_websocket_error(
            error_type="timeout",
            message="Connection timeout",
            connection_id="conn_123",
            error_details=error_details
        )

        mock_logger.log_error.assert_called_once_with(
            error_type="timeout",
            message="Connection timeout",
            connection_id="conn_123",
            user_id=None,
            conversation_id=None,
            error_details=error_details,
            level="error"
        )

    @patch('openhands.server.websocket.logging.websocket_logger')
    def test_log_websocket_metrics(self, mock_logger):
        """Test log_websocket_metrics convenience function."""
        metrics = {"connections": 10}

        log_websocket_metrics(
            metric_type="performance",
            message="Performance metrics",
            metrics=metrics
        )

        mock_logger.log_metrics.assert_called_once_with(
            metric_type="performance",
            message="Performance metrics",
            connection_id=None,
            user_id=None,
            conversation_id=None,
            metrics=metrics
        )


class TestIntegrationScenarios:
    """Test integration scenarios with correlation ID tracking."""

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_full_request_lifecycle_logging(self, mock_logger):
        """Test logging throughout a complete request lifecycle."""
        correlation_id = "lifecycle-test-123"
        connection_id = "conn_456"
        user_id = "user_789"
        conversation_id = "conv_012"

        with CorrelationIdManager.correlation_context(correlation_id):
            # Log connection
            log_websocket_connection(
                event_type="connect",
                message="User connecting",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id
            )

            # Log event processing
            log_websocket_event(
                event_type="message",
                message="Processing user message",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                event_data={"content": "Hello"},
                processing_time_ms=50.0
            )

            # Log metrics
            log_websocket_metrics(
                metric_type="performance",
                message="Connection metrics",
                connection_id=connection_id,
                metrics={"latency_ms": 25.0}
            )

            # Log disconnection
            log_websocket_connection(
                event_type="disconnect",
                message="User disconnecting",
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id
            )

        # Verify all calls were made with the same correlation ID
        assert mock_logger.info.call_count == 4  # 3 info calls + 1 metrics call

        for call in mock_logger.info.call_args_list:
            args, kwargs = call
            extra = kwargs["extra"]
            assert extra["correlation_id"] == correlation_id
            assert extra["connection_id"] == connection_id

    @patch('openhands.server.websocket.logging.openhands_logger')
    def test_error_scenario_with_context(self, mock_logger):
        """Test error logging with full context."""
        correlation_id = "error-test-789"

        with CorrelationIdManager.correlation_context(correlation_id):
            # Log initial connection
            log_websocket_connection(
                event_type="connect",
                message="Attempting connection",
                connection_id="conn_123"
            )

            # Log error
            log_websocket_error(
                error_type="authentication",
                message="Authentication failed",
                connection_id="conn_123",
                error_details={
                    "reason": "invalid_token",
                    "attempts": 3
                }
            )

        # Verify correlation ID is consistent
        info_call = mock_logger.info.call_args
        error_call = mock_logger.error.call_args

        assert info_call[1]["extra"]["correlation_id"] == correlation_id
        assert error_call[1]["extra"]["correlation_id"] == correlation_id
