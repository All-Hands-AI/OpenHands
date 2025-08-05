"""
Unit tests for WebSocket connection state management.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import redis.asyncio as redis

from openhands.server.websocket.connection_state import (
    ConnectionState,
    ConnectionStateManager,
    HealthStatus,
)


@pytest.fixture
def sample_connection_state():
    """Create a sample connection state for testing."""
    return ConnectionState(
        connection_id="test_conn_123",
        user_id="user_456",
        conversation_id="conv_789",
        connected_at=datetime(2024, 1, 1, 12, 0, 0),
        last_activity=datetime(2024, 1, 1, 12, 5, 0),
        last_event_id=42,
        client_info={"user_agent": "test_agent", "remote_addr": "127.0.0.1"},
        health_status=HealthStatus.HEALTHY,
        reconnection_count=0,
        error_count=0
    )


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock_client = AsyncMock(spec=redis.Redis)
    return mock_client


@pytest.fixture
def connection_manager(mock_redis_client):
    """Create a connection state manager with mocked Redis client."""
    manager = ConnectionStateManager()
    manager._redis_client = mock_redis_client
    return manager


class TestConnectionState:
    """Test ConnectionState data model."""

    def test_to_dict(self, sample_connection_state):
        """Test conversion to dictionary."""
        data = sample_connection_state.to_dict()

        assert data["connection_id"] == "test_conn_123"
        assert data["user_id"] == "user_456"
        assert data["conversation_id"] == "conv_789"
        assert data["connected_at"] == "2024-01-01T12:00:00"
        assert data["last_activity"] == "2024-01-01T12:05:00"
        assert data["last_event_id"] == 42
        assert data["client_info"] == {"user_agent": "test_agent", "remote_addr": "127.0.0.1"}
        assert data["health_status"] == "healthy"
        assert data["reconnection_count"] == 0
        assert data["error_count"] == 0

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "connection_id": "test_conn_123",
            "user_id": "user_456",
            "conversation_id": "conv_789",
            "connected_at": "2024-01-01T12:00:00",
            "last_activity": "2024-01-01T12:05:00",
            "last_event_id": 42,
            "client_info": {"user_agent": "test_agent", "remote_addr": "127.0.0.1"},
            "health_status": "healthy",
            "reconnection_count": 0,
            "error_count": 0
        }

        connection_state = ConnectionState.from_dict(data)

        assert connection_state.connection_id == "test_conn_123"
        assert connection_state.user_id == "user_456"
        assert connection_state.conversation_id == "conv_789"
        assert connection_state.connected_at == datetime(2024, 1, 1, 12, 0, 0)
        assert connection_state.last_activity == datetime(2024, 1, 1, 12, 5, 0)
        assert connection_state.last_event_id == 42
        assert connection_state.client_info == {"user_agent": "test_agent", "remote_addr": "127.0.0.1"}
        assert connection_state.health_status == HealthStatus.HEALTHY
        assert connection_state.reconnection_count == 0
        assert connection_state.error_count == 0


class TestConnectionStateManager:
    """Test ConnectionStateManager functionality."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        manager = ConnectionStateManager()

        assert manager.redis_url == "redis://localhost:6379"
        assert manager.redis_password is None
        assert manager._redis_client is None
        assert manager.key_prefix == "openhands:connection:"
        assert manager.connection_set_key == "openhands:connections:active"

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        manager = ConnectionStateManager(
            redis_url="redis://custom:6380",
            redis_password="secret"
        )

        assert manager.redis_url == "redis://custom:6380"
        assert manager.redis_password == "secret"

    def test_get_connection_key(self, connection_manager):
        """Test connection key generation."""
        key = connection_manager._get_connection_key("test_conn_123")
        assert key == "openhands:connection:test_conn_123"

    @pytest.mark.asyncio
    async def test_create_connection_state_success(self, connection_manager, mock_redis_client):
        """Test successful connection state creation."""
        mock_pipeline = AsyncMock()
        mock_redis_client.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_redis_client.pipeline.return_value.__aexit__.return_value = None
        mock_pipeline.execute.return_value = [True, True, True]

        with patch('openhands.server.websocket.connection_state.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            connection_state = await connection_manager.create_connection_state(
                connection_id="test_conn_123",
                user_id="user_456",
                conversation_id="conv_789",
                client_info={"user_agent": "test_agent"},
                last_event_id=42
            )

        assert connection_state.connection_id == "test_conn_123"
        assert connection_state.user_id == "user_456"
        assert connection_state.conversation_id == "conv_789"
        assert connection_state.connected_at == mock_now
        assert connection_state.last_activity == mock_now
        assert connection_state.last_event_id == 42
        assert connection_state.health_status == HealthStatus.HEALTHY
        assert connection_state.reconnection_count == 0
        assert connection_state.error_count == 0

        # Verify Redis operations
        mock_pipeline.hset.assert_called_once()
        mock_pipeline.sadd.assert_called_once()
        mock_pipeline.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_connection_state_redis_error(self, connection_manager, mock_redis_client):
        """Test connection state creation with Redis error."""
        mock_redis_client.pipeline.side_effect = redis.RedisError("Connection failed")

        with pytest.raises(redis.RedisError):
            await connection_manager.create_connection_state(
                connection_id="test_conn_123",
                user_id="user_456",
                conversation_id="conv_789",
                client_info={"user_agent": "test_agent"}
            )

    @pytest.mark.asyncio
    async def test_get_connection_state_success(self, connection_manager, mock_redis_client, sample_connection_state):
        """Test successful connection state retrieval."""
        mock_redis_client.hgetall = AsyncMock(return_value=sample_connection_state.to_dict())

        result = await connection_manager.get_connection_state("test_conn_123")

        assert result is not None
        assert result.connection_id == "test_conn_123"
        assert result.user_id == "user_456"
        assert result.health_status == HealthStatus.HEALTHY

        mock_redis_client.hgetall.assert_called_once_with("openhands:connection:test_conn_123")

    @pytest.mark.asyncio
    async def test_get_connection_state_not_found(self, connection_manager, mock_redis_client):
        """Test connection state retrieval when not found."""
        mock_redis_client.hgetall = AsyncMock(return_value={})

        result = await connection_manager.get_connection_state("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_connection_state_redis_error(self, connection_manager, mock_redis_client):
        """Test connection state retrieval with Redis error."""
        mock_redis_client.hgetall.side_effect = redis.RedisError("Connection failed")

        with pytest.raises(redis.RedisError):
            await connection_manager.get_connection_state("test_conn_123")

    @pytest.mark.asyncio
    async def test_get_connection_state_corrupted_data(self, connection_manager, mock_redis_client):
        """Test connection state retrieval with corrupted data."""
        # Return data with invalid datetime format
        mock_redis_client.hgetall = AsyncMock(return_value={
            "connection_id": "test_conn_123",
            "connected_at": "invalid_datetime",
            "last_activity": "2024-01-01T12:05:00"
        })

        result = await connection_manager.get_connection_state("test_conn_123")

        # Should return None for corrupted data
        assert result is None

    @pytest.mark.asyncio
    async def test_update_connection_state_success(self, connection_manager, mock_redis_client, sample_connection_state):
        """Test successful connection state update."""
        mock_pipeline = AsyncMock()
        mock_redis_client.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_redis_client.pipeline.return_value.__aexit__.return_value = None
        mock_pipeline.execute.return_value = [True, True, True]

        await connection_manager.update_connection_state(sample_connection_state)

        # Verify Redis operations
        mock_pipeline.hset.assert_called_once()
        mock_pipeline.sadd.assert_called_once()
        mock_pipeline.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_last_activity_success(self, connection_manager, mock_redis_client):
        """Test successful last activity update."""
        mock_redis_client.hset = AsyncMock()

        with patch('openhands.server.websocket.connection_state.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1, 12, 10, 0)
            mock_datetime.utcnow.return_value = mock_now

            await connection_manager.update_last_activity("test_conn_123")

        mock_redis_client.hset.assert_called_once_with(
            "openhands:connection:test_conn_123",
            "last_activity",
            "2024-01-01T12:10:00"
        )

    @pytest.mark.asyncio
    async def test_increment_error_count_success(self, connection_manager, mock_redis_client):
        """Test successful error count increment."""
        mock_redis_client.hincrby = AsyncMock(return_value=3)

        result = await connection_manager.increment_error_count("test_conn_123")

        assert result == 3
        mock_redis_client.hincrby.assert_called_once_with(
            "openhands:connection:test_conn_123",
            "error_count",
            1
        )

    @pytest.mark.asyncio
    async def test_increment_reconnection_count_success(self, connection_manager, mock_redis_client):
        """Test successful reconnection count increment."""
        mock_redis_client.hincrby = AsyncMock(return_value=2)

        result = await connection_manager.increment_reconnection_count("test_conn_123")

        assert result == 2
        mock_redis_client.hincrby.assert_called_once_with(
            "openhands:connection:test_conn_123",
            "reconnection_count",
            1
        )

    @pytest.mark.asyncio
    async def test_delete_connection_state_success(self, connection_manager, mock_redis_client):
        """Test successful connection state deletion."""
        mock_pipeline = AsyncMock()
        mock_redis_client.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_redis_client.pipeline.return_value.__aexit__.return_value = None
        mock_pipeline.execute.return_value = [1, 1]  # Both operations successful

        result = await connection_manager.delete_connection_state("test_conn_123")

        assert result is True
        mock_pipeline.delete.assert_called_once_with("openhands:connection:test_conn_123")
        mock_pipeline.srem.assert_called_once_with("openhands:connections:active", "test_conn_123")

    @pytest.mark.asyncio
    async def test_delete_connection_state_not_found(self, connection_manager, mock_redis_client):
        """Test connection state deletion when not found."""
        mock_pipeline = AsyncMock()
        mock_redis_client.pipeline.return_value.__aenter__.return_value = mock_pipeline
        mock_redis_client.pipeline.return_value.__aexit__.return_value = None
        mock_pipeline.execute.return_value = [0, 0]  # Connection didn't exist

        result = await connection_manager.delete_connection_state("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_active_connections_success(self, connection_manager, mock_redis_client):
        """Test successful retrieval of all active connections."""
        mock_redis_client.smembers = AsyncMock(return_value={"conn_1", "conn_2", "conn_3"})

        result = await connection_manager.get_all_active_connections()

        assert set(result) == {"conn_1", "conn_2", "conn_3"}
        mock_redis_client.smembers.assert_called_once_with("openhands:connections:active")

    @pytest.mark.asyncio
    async def test_get_connections_by_user_success(self, connection_manager):
        """Test successful retrieval of connections by user."""
        # Mock the methods we need
        connection_manager.get_all_active_connections = AsyncMock(return_value=["conn_1", "conn_2", "conn_3"])

        # Mock connection states
        connection_states = {
            "conn_1": ConnectionState(
                connection_id="conn_1", user_id="user_456", conversation_id="conv_1",
                connected_at=datetime.utcnow(), last_activity=datetime.utcnow(),
                last_event_id=1, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_2": ConnectionState(
                connection_id="conn_2", user_id="user_789", conversation_id="conv_2",
                connected_at=datetime.utcnow(), last_activity=datetime.utcnow(),
                last_event_id=2, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_3": ConnectionState(
                connection_id="conn_3", user_id="user_456", conversation_id="conv_3",
                connected_at=datetime.utcnow(), last_activity=datetime.utcnow(),
                last_event_id=3, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            )
        }

        async def mock_get_connection_state(conn_id):
            return connection_states.get(conn_id)

        connection_manager.get_connection_state = mock_get_connection_state

        result = await connection_manager.get_connections_by_user("user_456")

        assert len(result) == 2
        assert all(conn.user_id == "user_456" for conn in result)
        assert {conn.connection_id for conn in result} == {"conn_1", "conn_3"}

    @pytest.mark.asyncio
    async def test_get_stale_connections_success(self, connection_manager):
        """Test successful retrieval of stale connections."""
        # Mock the methods we need
        connection_manager.get_all_active_connections = AsyncMock(return_value=["conn_1", "conn_2", "conn_3"])

        # Create connection states with different activity times
        now = datetime.utcnow()
        old_time = now - timedelta(minutes=10)  # 10 minutes ago (stale)
        recent_time = now - timedelta(minutes=2)  # 2 minutes ago (fresh)

        connection_states = {
            "conn_1": ConnectionState(
                connection_id="conn_1", user_id="user_1", conversation_id="conv_1",
                connected_at=old_time, last_activity=old_time,  # Stale
                last_event_id=1, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_2": ConnectionState(
                connection_id="conn_2", user_id="user_2", conversation_id="conv_2",
                connected_at=recent_time, last_activity=recent_time,  # Fresh
                last_event_id=2, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            ),
            "conn_3": ConnectionState(
                connection_id="conn_3", user_id="user_3", conversation_id="conv_3",
                connected_at=old_time, last_activity=old_time,  # Stale
                last_event_id=3, client_info={}, health_status=HealthStatus.HEALTHY,
                reconnection_count=0, error_count=0
            )
        }

        async def mock_get_connection_state(conn_id):
            return connection_states.get(conn_id)

        connection_manager.get_connection_state = mock_get_connection_state

        result = await connection_manager.get_stale_connections(timeout_seconds=300)  # 5 minutes

        assert set(result) == {"conn_1", "conn_3"}

    @pytest.mark.asyncio
    async def test_close_connection(self, connection_manager, mock_redis_client):
        """Test closing Redis connection."""
        await connection_manager.close()

        mock_redis_client.close.assert_called_once()
        assert connection_manager._redis_client is None
