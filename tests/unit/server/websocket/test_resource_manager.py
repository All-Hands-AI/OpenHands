"""
Unit tests for WebSocket connection resource management.
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
from openhands.server.websocket.resource_manager import (
    CleanupConfig,
    ConnectionResourceManager,
    ResourceUsage,
)


@pytest.fixture
def cleanup_config():
    """Create a cleanup configuration for testing."""
    return CleanupConfig(
        max_connections_per_user=3,
        max_total_connections=10,
        memory_threshold_mb=50,
        cpu_threshold_percent=75.0,
        cleanup_interval_seconds=5,
        graceful_shutdown_timeout_seconds=10,
        force_cleanup_after_seconds=30,
    )


@pytest.fixture
def mock_connection_state_manager():
    """Create a mock connection state manager."""
    return AsyncMock(spec=ConnectionStateManager)


@pytest.fixture
def resource_manager(mock_connection_state_manager, cleanup_config):
    """Create a resource manager with mocked dependencies."""
    return ConnectionResourceManager(mock_connection_state_manager, cleanup_config)


@pytest.fixture
def sample_resource_usage():
    """Create a sample resource usage for testing."""
    return ResourceUsage(
        connection_id="test_conn_123",
        memory_usage_bytes=25 * 1024 * 1024,  # 25 MB
        cpu_usage_percent=50.0,
        message_count=100,
        error_count=2,
        last_updated=datetime.utcnow(),
    )


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


class TestResourceUsage:
    """Test ResourceUsage data model."""

    def test_to_dict(self, sample_resource_usage):
        """Test conversion to dictionary."""
        data = sample_resource_usage.to_dict()

        assert data["connection_id"] == "test_conn_123"
        assert data["memory_usage_bytes"] == 25 * 1024 * 1024
        assert data["cpu_usage_percent"] == 50.0
        assert data["message_count"] == 100
        assert data["error_count"] == 2
        assert "last_updated" in data


class TestCleanupConfig:
    """Test CleanupConfig functionality."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CleanupConfig()

        assert config.max_connections_per_user == 10
        assert config.max_total_connections == 1000
        assert config.memory_threshold_mb == 100
        assert config.cpu_threshold_percent == 80.0
        assert config.cleanup_interval_seconds == 60
        assert config.graceful_shutdown_timeout_seconds == 30
        assert config.force_cleanup_after_seconds == 300

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CleanupConfig(
            max_connections_per_user=5,
            max_total_connections=500,
            memory_threshold_mb=200,
            cpu_threshold_percent=90.0,
            cleanup_interval_seconds=30,
            graceful_shutdown_timeout_seconds=15,
            force_cleanup_after_seconds=120,
        )

        assert config.max_connections_per_user == 5
        assert config.max_total_connections == 500
        assert config.memory_threshold_mb == 200
        assert config.cpu_threshold_percent == 90.0
        assert config.cleanup_interval_seconds == 30
        assert config.graceful_shutdown_timeout_seconds == 15
        assert config.force_cleanup_after_seconds == 120


class TestConnectionResourceManager:
    """Test ConnectionResourceManager functionality."""

    def test_init_default_config(self, mock_connection_state_manager):
        """Test initialization with default configuration."""
        manager = ConnectionResourceManager(mock_connection_state_manager)

        assert manager.connection_state_manager == mock_connection_state_manager
        assert manager.config is not None
        assert manager.config.max_connections_per_user == 10
        assert manager._cleanup_task is None
        assert manager._is_running is False

    def test_init_custom_config(self, mock_connection_state_manager, cleanup_config):
        """Test initialization with custom configuration."""
        manager = ConnectionResourceManager(mock_connection_state_manager, cleanup_config)

        assert manager.connection_state_manager == mock_connection_state_manager
        assert manager.config == cleanup_config
        assert manager.config.max_connections_per_user == 3

    @pytest.mark.asyncio
    async def test_track_resource_usage(self, resource_manager):
        """Test tracking resource usage for a connection."""
        await resource_manager.track_resource_usage(
            connection_id="test_conn_123",
            memory_usage_bytes=50 * 1024 * 1024,  # 50 MB
            cpu_usage_percent=60.0,
            message_count=200,
            error_count=5,
        )

        usage = await resource_manager.get_resource_usage("test_conn_123")
        assert usage is not None
        assert usage.connection_id == "test_conn_123"
        assert usage.memory_usage_bytes == 50 * 1024 * 1024
        assert usage.cpu_usage_percent == 60.0
        assert usage.message_count == 200
        assert usage.error_count == 5

    @pytest.mark.asyncio
    async def test_get_resource_usage_not_found(self, resource_manager):
        """Test getting resource usage for non-existent connection."""
        usage = await resource_manager.get_resource_usage("nonexistent")
        assert usage is None

    @pytest.mark.asyncio
    async def test_get_all_resource_usage(self, resource_manager):
        """Test getting all resource usage."""
        # Track usage for multiple connections
        await resource_manager.track_resource_usage("conn_1", memory_usage_bytes=10 * 1024 * 1024)
        await resource_manager.track_resource_usage("conn_2", memory_usage_bytes=20 * 1024 * 1024)
        await resource_manager.track_resource_usage("conn_3", memory_usage_bytes=30 * 1024 * 1024)

        all_usage = await resource_manager.get_all_resource_usage()

        assert len(all_usage) == 3
        assert "conn_1" in all_usage
        assert "conn_2" in all_usage
        assert "conn_3" in all_usage
        assert all_usage["conn_1"].memory_usage_bytes == 10 * 1024 * 1024
        assert all_usage["conn_2"].memory_usage_bytes == 20 * 1024 * 1024
        assert all_usage["conn_3"].memory_usage_bytes == 30 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_initiate_graceful_shutdown(self, resource_manager, mock_connection_state_manager, sample_connection_state):
        """Test initiating graceful shutdown for a connection."""
        mock_connection_state_manager.get_connection_state.return_value = sample_connection_state
        mock_connection_state_manager.update_connection_state = AsyncMock()

        result = await resource_manager.initiate_graceful_shutdown("test_conn_123", "test_reason")

        assert result is True
        assert "test_conn_123" in resource_manager._shutdown_connections
        mock_connection_state_manager.update_connection_state.assert_called_once()

        # Check that connection state was updated to DISCONNECTED
        updated_state = mock_connection_state_manager.update_connection_state.call_args[0][0]
        assert updated_state.health_status == HealthStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_force_cleanup_connection(self, resource_manager, mock_connection_state_manager):
        """Test force cleanup of a connection."""
        # Add some tracking data
        await resource_manager.track_resource_usage("test_conn_123", memory_usage_bytes=10 * 1024 * 1024)
        resource_manager._shutdown_connections.add("test_conn_123")

        mock_connection_state_manager.delete_connection_state = AsyncMock()

        result = await resource_manager.force_cleanup_connection("test_conn_123", "test_reason")

        assert result is True
        assert "test_conn_123" not in resource_manager._resource_usage
        assert "test_conn_123" not in resource_manager._shutdown_connections
        mock_connection_state_manager.delete_connection_state.assert_called_once_with("test_conn_123")

    @pytest.mark.asyncio
    async def test_cleanup_connections_by_user_limit(self, resource_manager, mock_connection_state_manager):
        """Test cleanup of connections that exceed per-user limits."""
        # Mock connections for a user that exceeds the limit (3 connections max)
        connection_states = {
            "conn_1": ConnectionState(
                connection_id="conn_1", user_id="user_123", conversation_id="conv_1",
                connected_at=datetime.utcnow() - timedelta(minutes=10),
                last_activity=datetime.utcnow() - timedelta(minutes=8),  # Oldest
                last_event_id=1, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_2": ConnectionState(
                connection_id="conn_2", user_id="user_123", conversation_id="conv_2",
                connected_at=datetime.utcnow() - timedelta(minutes=5),
                last_activity=datetime.utcnow() - timedelta(minutes=3),  # Middle
                last_event_id=2, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_3": ConnectionState(
                connection_id="conn_3", user_id="user_123", conversation_id="conv_3",
                connected_at=datetime.utcnow() - timedelta(minutes=2),
                last_activity=datetime.utcnow() - timedelta(minutes=1),  # Newest
                last_event_id=3, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_4": ConnectionState(
                connection_id="conn_4", user_id="user_123", conversation_id="conv_4",
                connected_at=datetime.utcnow() - timedelta(minutes=1),
                last_activity=datetime.utcnow() - timedelta(seconds=30),  # Very new
                last_event_id=4, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
        }

        mock_connection_state_manager.get_all_active_connections.return_value = list(connection_states.keys())

        async def mock_get_connection_state(conn_id):
            return connection_states.get(conn_id)

        mock_connection_state_manager.get_connection_state.side_effect = mock_get_connection_state
        mock_connection_state_manager.update_connection_state = AsyncMock()

        result = await resource_manager.cleanup_connections_by_user_limit()

        # Should clean up 1 connection (4 total - 3 max = 1 excess)
        assert len(result) == 1
        # Should clean up the oldest connection (conn_1)
        assert "conn_1" in result
        assert "conn_1" in resource_manager._shutdown_connections

    @pytest.mark.asyncio
    async def test_cleanup_connections_by_resource_usage_memory(self, resource_manager):
        """Test cleanup of connections that exceed memory usage threshold."""
        # Track connections with different memory usage (threshold is 50MB)
        await resource_manager.track_resource_usage("conn_1", memory_usage_bytes=30 * 1024 * 1024)  # 30MB - OK
        await resource_manager.track_resource_usage("conn_2", memory_usage_bytes=60 * 1024 * 1024)  # 60MB - Exceeds
        await resource_manager.track_resource_usage("conn_3", memory_usage_bytes=80 * 1024 * 1024)  # 80MB - Exceeds

        # Mock the initiate_graceful_shutdown method
        resource_manager.initiate_graceful_shutdown = AsyncMock(return_value=True)

        result = await resource_manager.cleanup_connections_by_resource_usage()

        # Should clean up 2 connections that exceed memory threshold
        assert len(result) == 2
        assert set(result) == {"conn_2", "conn_3"}
        assert resource_manager.initiate_graceful_shutdown.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_connections_by_resource_usage_cpu(self, resource_manager):
        """Test cleanup of connections that exceed CPU usage threshold."""
        # Track connections with different CPU usage (threshold is 75%)
        await resource_manager.track_resource_usage("conn_1", cpu_usage_percent=50.0)  # OK
        await resource_manager.track_resource_usage("conn_2", cpu_usage_percent=80.0)  # Exceeds
        await resource_manager.track_resource_usage("conn_3", cpu_usage_percent=90.0)  # Exceeds

        # Mock the initiate_graceful_shutdown method
        resource_manager.initiate_graceful_shutdown = AsyncMock(return_value=True)

        result = await resource_manager.cleanup_connections_by_resource_usage()

        # Should clean up 2 connections that exceed CPU threshold
        assert len(result) == 2
        assert set(result) == {"conn_2", "conn_3"}
        assert resource_manager.initiate_graceful_shutdown.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_stale_resource_tracking(self, resource_manager, mock_connection_state_manager):
        """Test cleanup of stale resource tracking entries."""
        # Track usage for multiple connections
        await resource_manager.track_resource_usage("conn_1", memory_usage_bytes=10 * 1024 * 1024)
        await resource_manager.track_resource_usage("conn_2", memory_usage_bytes=20 * 1024 * 1024)
        await resource_manager.track_resource_usage("conn_3", memory_usage_bytes=30 * 1024 * 1024)

        # Mock that only conn_1 and conn_3 are still active
        mock_connection_state_manager.get_all_active_connections.return_value = ["conn_1", "conn_3"]

        result = await resource_manager.cleanup_stale_resource_tracking()

        # Should clean up 1 stale entry (conn_2)
        assert result == 1
        assert "conn_1" in resource_manager._resource_usage
        assert "conn_2" not in resource_manager._resource_usage
        assert "conn_3" in resource_manager._resource_usage

    @pytest.mark.asyncio
    async def test_get_resource_metrics(self, resource_manager):
        """Test getting resource metrics."""
        # Track usage for multiple connections
        await resource_manager.track_resource_usage("conn_1", memory_usage_bytes=10 * 1024 * 1024, cpu_usage_percent=30.0, message_count=100, error_count=1)
        await resource_manager.track_resource_usage("conn_2", memory_usage_bytes=60 * 1024 * 1024, cpu_usage_percent=80.0, message_count=200, error_count=3)  # High memory and CPU
        await resource_manager.track_resource_usage("conn_3", memory_usage_bytes=20 * 1024 * 1024, cpu_usage_percent=40.0, message_count=150, error_count=0)

        # Add a connection to shutdown tracking
        resource_manager._shutdown_connections.add("conn_4")

        metrics = await resource_manager.get_resource_metrics()

        assert metrics["total_connections"] == 3
        assert metrics["total_memory_mb"] == (10 + 60 + 20)  # 90 MB total
        assert metrics["average_cpu_percent"] == (30.0 + 80.0 + 40.0) / 3  # 50% average
        assert metrics["total_messages"] == 100 + 200 + 150  # 450 total
        assert metrics["total_errors"] == 1 + 3 + 0  # 4 total
        assert metrics["high_memory_connections"] == 1  # conn_2 exceeds 50MB threshold
        assert metrics["high_cpu_connections"] == 1  # conn_2 exceeds 75% threshold
        assert metrics["shutdown_pending_connections"] == 1  # conn_4

    @pytest.mark.asyncio
    async def test_get_resource_metrics_empty(self, resource_manager):
        """Test getting resource metrics when no connections are tracked."""
        metrics = await resource_manager.get_resource_metrics()

        assert metrics["total_connections"] == 0
        assert metrics["total_memory_mb"] == 0.0
        assert metrics["average_cpu_percent"] == 0.0
        assert metrics["total_messages"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["high_memory_connections"] == 0
        assert metrics["high_cpu_connections"] == 0
        assert metrics["shutdown_pending_connections"] == 0

    @pytest.mark.asyncio
    async def test_start_stop_resource_management(self, resource_manager):
        """Test starting and stopping the resource management task."""
        assert not resource_manager.is_running()

        # Mock the cleanup loop to avoid infinite loop
        resource_manager._cleanup_loop = AsyncMock()

        # Start resource management
        await resource_manager.start_resource_management()
        assert resource_manager.is_running()
        assert resource_manager._cleanup_task is not None

        # Stop resource management
        await resource_manager.stop_resource_management()
        assert not resource_manager.is_running()
        assert resource_manager._cleanup_task is None

    @pytest.mark.asyncio
    async def test_start_resource_management_already_running(self, resource_manager):
        """Test starting resource management when it's already running."""
        resource_manager._is_running = True

        await resource_manager.start_resource_management()

        # Should not create a new task
        assert resource_manager._cleanup_task is None

    @pytest.mark.asyncio
    async def test_stop_resource_management_not_running(self, resource_manager):
        """Test stopping resource management when it's not running."""
        assert not resource_manager.is_running()

        # Should not raise an exception
        await resource_manager.stop_resource_management()
        assert not resource_manager.is_running()

    @pytest.mark.asyncio
    async def test_force_cleanup_after_timeout(self, resource_manager):
        """Test force cleanup after graceful shutdown timeout."""
        # Add connection to shutdown tracking
        resource_manager._shutdown_connections.add("test_conn_123")

        # Mock force_cleanup_connection
        resource_manager.force_cleanup_connection = AsyncMock(return_value=True)

        # Start the timeout task with a very short timeout for testing
        resource_manager.config.graceful_shutdown_timeout_seconds = 0.1

        # Start the timeout task
        task = asyncio.create_task(resource_manager._force_cleanup_after_timeout("test_conn_123"))

        # Wait for the timeout
        await asyncio.sleep(0.2)

        # Check that force cleanup was called
        resource_manager.force_cleanup_connection.assert_called_once_with("test_conn_123", "graceful_shutdown_timeout")

        # Clean up the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
