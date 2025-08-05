"""
Unit tests for WebSocket connection health monitoring.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.server.websocket.connection_state import (
    ConnectionState,
    ConnectionStateManager,
    HealthStatus,
)
from openhands.server.websocket.health_monitor import (
    ConnectionHealthMonitor,
    HealthCheckConfig,
)


@pytest.fixture
def health_config():
    """Create a health check configuration for testing."""
    return HealthCheckConfig(
        check_interval_seconds=5,
        connection_timeout_seconds=60,
        max_consecutive_failures=2,
        cleanup_stale_connections=True,
        stale_connection_threshold_seconds=120,
    )


@pytest.fixture
def mock_connection_state_manager():
    """Create a mock connection state manager."""
    return AsyncMock(spec=ConnectionStateManager)


@pytest.fixture
def health_monitor(mock_connection_state_manager, health_config):
    """Create a health monitor with mocked dependencies."""
    return ConnectionHealthMonitor(mock_connection_state_manager, health_config)


@pytest.fixture
def sample_connection_state():
    """Create a sample connection state for testing."""
    return ConnectionState(
        connection_id="test_conn_123",
        user_id="user_456",
        conversation_id="conv_789",
        connected_at=datetime.utcnow() - timedelta(minutes=5),
        last_activity=datetime.utcnow() - timedelta(seconds=30),
        last_event_id=42,
        client_info={"user_agent": "test_agent"},
        health_status=HealthStatus.HEALTHY,
        reconnection_count=0,
        error_count=0
    )


class TestHealthCheckConfig:
    """Test HealthCheckConfig functionality."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HealthCheckConfig()

        assert config.check_interval_seconds == 30
        assert config.connection_timeout_seconds == 300
        assert config.max_consecutive_failures == 3
        assert config.cleanup_stale_connections is True
        assert config.stale_connection_threshold_seconds == 600

    def test_custom_values(self):
        """Test custom configuration values."""
        config = HealthCheckConfig(
            check_interval_seconds=10,
            connection_timeout_seconds=120,
            max_consecutive_failures=5,
            cleanup_stale_connections=False,
            stale_connection_threshold_seconds=300,
        )

        assert config.check_interval_seconds == 10
        assert config.connection_timeout_seconds == 120
        assert config.max_consecutive_failures == 5
        assert config.cleanup_stale_connections is False
        assert config.stale_connection_threshold_seconds == 300


class TestConnectionHealthMonitor:
    """Test ConnectionHealthMonitor functionality."""

    def test_init_default_config(self, mock_connection_state_manager):
        """Test initialization with default configuration."""
        monitor = ConnectionHealthMonitor(mock_connection_state_manager)

        assert monitor.connection_state_manager == mock_connection_state_manager
        assert monitor.config is not None
        assert monitor.config.check_interval_seconds == 30
        assert monitor._monitoring_task is None
        assert monitor._is_running is False

    def test_init_custom_config(self, mock_connection_state_manager, health_config):
        """Test initialization with custom configuration."""
        monitor = ConnectionHealthMonitor(mock_connection_state_manager, health_config)

        assert monitor.connection_state_manager == mock_connection_state_manager
        assert monitor.config == health_config
        assert monitor.config.check_interval_seconds == 5

    @pytest.mark.asyncio
    async def test_check_connection_health_healthy(self, health_monitor, mock_connection_state_manager, sample_connection_state):
        """Test health check for a healthy connection."""
        mock_connection_state_manager.get_connection_state.return_value = sample_connection_state
        mock_connection_state_manager.update_connection_state = AsyncMock()

        result = await health_monitor.check_connection_health("test_conn_123")

        assert result == HealthStatus.HEALTHY
        mock_connection_state_manager.get_connection_state.assert_called_once_with("test_conn_123")
        # Should not update state since it's already healthy
        mock_connection_state_manager.update_connection_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_connection_health_degraded_errors(self, health_monitor, mock_connection_state_manager, sample_connection_state):
        """Test health check for a connection with errors (degraded)."""
        sample_connection_state.error_count = 1
        mock_connection_state_manager.get_connection_state.return_value = sample_connection_state
        mock_connection_state_manager.update_connection_state = AsyncMock()

        result = await health_monitor.check_connection_health("test_conn_123")

        assert result == HealthStatus.DEGRADED
        mock_connection_state_manager.update_connection_state.assert_called_once()
        # Check that the connection state was updated
        updated_state = mock_connection_state_manager.update_connection_state.call_args[0][0]
        assert updated_state.health_status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_connection_health_unhealthy_timeout(self, health_monitor, mock_connection_state_manager, sample_connection_state):
        """Test health check for a timed out connection (unhealthy)."""
        # Set last activity to more than timeout threshold ago
        sample_connection_state.last_activity = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes ago, timeout is 60s
        mock_connection_state_manager.get_connection_state.return_value = sample_connection_state
        mock_connection_state_manager.update_connection_state = AsyncMock()

        result = await health_monitor.check_connection_health("test_conn_123")

        assert result == HealthStatus.UNHEALTHY
        mock_connection_state_manager.update_connection_state.assert_called_once()
        # Check that the connection state was updated
        updated_state = mock_connection_state_manager.update_connection_state.call_args[0][0]
        assert updated_state.health_status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_connection_health_not_found(self, health_monitor, mock_connection_state_manager):
        """Test health check for a connection that doesn't exist."""
        mock_connection_state_manager.get_connection_state.return_value = None

        result = await health_monitor.check_connection_health("nonexistent")

        assert result == HealthStatus.DISCONNECTED
        mock_connection_state_manager.get_connection_state.assert_called_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_check_connection_health_exception(self, health_monitor, mock_connection_state_manager):
        """Test health check when an exception occurs."""
        mock_connection_state_manager.get_connection_state.side_effect = Exception("Redis error")

        result = await health_monitor.check_connection_health("test_conn_123")

        assert result == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_check_all_connections_health(self, health_monitor, mock_connection_state_manager):
        """Test checking health of all connections."""
        # Mock active connections
        mock_connection_state_manager.get_all_active_connections.return_value = ["conn_1", "conn_2", "conn_3"]

        # Mock health check results
        health_monitor.check_connection_health = AsyncMock()
        health_monitor.check_connection_health.side_effect = [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY
        ]

        result = await health_monitor.check_all_connections_health()

        assert len(result) == 3
        assert result["conn_1"] == HealthStatus.HEALTHY
        assert result["conn_2"] == HealthStatus.DEGRADED
        assert result["conn_3"] == HealthStatus.UNHEALTHY

        # Verify all connections were checked
        assert health_monitor.check_connection_health.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_unhealthy_connections(self, health_monitor, mock_connection_state_manager):
        """Test cleanup of unhealthy connections."""
        # Mock health check results
        health_monitor.check_all_connections_health = AsyncMock(return_value={
            "conn_1": HealthStatus.HEALTHY,
            "conn_2": HealthStatus.UNHEALTHY,
            "conn_3": HealthStatus.DEGRADED,
            "conn_4": HealthStatus.UNHEALTHY,
        })

        mock_connection_state_manager.delete_connection_state = AsyncMock()

        result = await health_monitor.cleanup_unhealthy_connections()

        # Should clean up the 2 unhealthy connections
        assert len(result) == 2
        assert set(result) == {"conn_2", "conn_4"}

        # Verify delete was called for unhealthy connections
        assert mock_connection_state_manager.delete_connection_state.call_count == 2
        delete_calls = [call[0][0] for call in mock_connection_state_manager.delete_connection_state.call_args_list]
        assert set(delete_calls) == {"conn_2", "conn_4"}

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(self, health_monitor, mock_connection_state_manager):
        """Test cleanup of stale connections."""
        mock_connection_state_manager.get_stale_connections.return_value = ["stale_1", "stale_2"]
        mock_connection_state_manager.delete_connection_state = AsyncMock()

        result = await health_monitor.cleanup_stale_connections()

        assert len(result) == 2
        assert set(result) == {"stale_1", "stale_2"}

        # Verify get_stale_connections was called with correct threshold
        mock_connection_state_manager.get_stale_connections.assert_called_once_with(
            timeout_seconds=120  # From health_config fixture
        )

        # Verify delete was called for stale connections
        assert mock_connection_state_manager.delete_connection_state.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections_disabled(self, mock_connection_state_manager):
        """Test that stale connection cleanup can be disabled."""
        config = HealthCheckConfig(cleanup_stale_connections=False)
        monitor = ConnectionHealthMonitor(mock_connection_state_manager, config)

        result = await monitor.cleanup_stale_connections()

        assert result == []
        mock_connection_state_manager.get_stale_connections.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_connection_metrics(self, health_monitor):
        """Test getting connection health metrics."""
        # Mock health check results
        health_monitor.check_all_connections_health = AsyncMock(return_value={
            "conn_1": HealthStatus.HEALTHY,
            "conn_2": HealthStatus.HEALTHY,
            "conn_3": HealthStatus.DEGRADED,
            "conn_4": HealthStatus.UNHEALTHY,
            "conn_5": HealthStatus.DISCONNECTED,
        })

        result = await health_monitor.get_connection_metrics()

        assert result["total_connections"] == 5
        assert result["healthy_connections"] == 2
        assert result["degraded_connections"] == 1
        assert result["unhealthy_connections"] == 1
        assert result["disconnected_connections"] == 1

    @pytest.mark.asyncio
    async def test_get_connection_metrics_exception(self, health_monitor):
        """Test getting connection metrics when an exception occurs."""
        health_monitor.check_all_connections_health = AsyncMock(side_effect=Exception("Error"))

        result = await health_monitor.get_connection_metrics()

        # Should return zero metrics on error
        assert result["total_connections"] == 0
        assert result["healthy_connections"] == 0
        assert result["degraded_connections"] == 0
        assert result["unhealthy_connections"] == 0
        assert result["disconnected_connections"] == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, health_monitor):
        """Test starting and stopping the monitoring task."""
        assert not health_monitor.is_running()

        # Mock the monitoring loop to avoid infinite loop
        health_monitor._monitoring_loop = AsyncMock()

        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor.is_running()
        assert health_monitor._monitoring_task is not None

        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert not health_monitor.is_running()
        assert health_monitor._monitoring_task is None

    @pytest.mark.asyncio
    async def test_start_monitoring_already_running(self, health_monitor):
        """Test starting monitoring when it's already running."""
        health_monitor._is_running = True

        await health_monitor.start_monitoring()

        # Should not create a new task
        assert health_monitor._monitoring_task is None

    @pytest.mark.asyncio
    async def test_stop_monitoring_not_running(self, health_monitor):
        """Test stopping monitoring when it's not running."""
        assert not health_monitor.is_running()

        # Should not raise an exception
        await health_monitor.stop_monitoring()
        assert not health_monitor.is_running()

    @pytest.mark.asyncio
    async def test_monitoring_loop_cancellation(self, health_monitor, mock_connection_state_manager):
        """Test that the monitoring loop handles cancellation gracefully."""
        # Start the actual monitoring loop
        await health_monitor.start_monitoring()

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Stop monitoring (should cancel the task)
        await health_monitor.stop_monitoring()

        assert not health_monitor.is_running()
        assert health_monitor._monitoring_task is None
