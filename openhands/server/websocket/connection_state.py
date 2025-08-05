"""
WebSocket Connection State Management

This module provides connection state tracking with Redis backend for
websocket connections in the OpenHands application.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from openhands.core.logger import openhands_logger as logger


class HealthStatus(Enum):
    """Connection health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


@dataclass
class ConnectionState:
    """Data model for websocket connection state."""

    connection_id: str
    user_id: str
    conversation_id: str
    connected_at: datetime
    last_activity: datetime
    last_event_id: int
    client_info: Dict[str, Any]
    health_status: HealthStatus
    reconnection_count: int
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection state to dictionary for Redis storage."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['connected_at'] = self.connected_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['health_status'] = self.health_status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionState':
        """Create ConnectionState from dictionary retrieved from Redis."""
        # Convert ISO format strings back to datetime objects
        data['connected_at'] = datetime.fromisoformat(data['connected_at'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        data['health_status'] = HealthStatus(data['health_status'])
        return cls(**data)


class ConnectionStateManager:
    """Manages websocket connection state with Redis persistence."""

    def __init__(self, redis_url: Optional[str] = None, redis_password: Optional[str] = None):
        """
        Initialize connection state manager.

        Args:
            redis_url: Redis connection URL (defaults to localhost)
            redis_password: Redis password if required
        """
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_password = redis_password
        self._redis_client: Optional[redis.Redis] = None
        self.key_prefix = "openhands:connection:"
        self.connection_set_key = "openhands:connections:active"

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client connection."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._redis_client

    def _get_connection_key(self, connection_id: str) -> str:
        """Generate Redis key for connection state."""
        return f"{self.key_prefix}{connection_id}"

    async def create_connection_state(
        self,
        connection_id: str,
        user_id: str,
        conversation_id: str,
        client_info: Dict[str, Any],
        last_event_id: int = -1
    ) -> ConnectionState:
        """
        Create and store new connection state.

        Args:
            connection_id: Unique connection identifier
            user_id: User identifier
            conversation_id: Conversation identifier
            client_info: Client information (user agent, IP, etc.)
            last_event_id: Last processed event ID

        Returns:
            Created ConnectionState instance

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            now = datetime.utcnow()
            connection_state = ConnectionState(
                connection_id=connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                connected_at=now,
                last_activity=now,
                last_event_id=last_event_id,
                client_info=client_info,
                health_status=HealthStatus.HEALTHY,
                reconnection_count=0,
                error_count=0
            )

            await self._store_connection_state(connection_state)

            logger.info(
                f"Created connection state for {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id
                }
            )

            return connection_state

        except redis.RedisError as e:
            logger.error(
                f"Failed to create connection state for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def get_connection_state(self, connection_id: str) -> Optional[ConnectionState]:
        """
        Retrieve connection state from Redis.

        Args:
            connection_id: Connection identifier

        Returns:
            ConnectionState if found, None otherwise

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            key = self._get_connection_key(connection_id)

            data = await redis_client.hgetall(key)
            if not data:
                return None

            return ConnectionState.from_dict(data)

        except redis.RedisError as e:
            logger.error(
                f"Failed to get connection state for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
        except (ValueError, KeyError) as e:
            logger.error(
                f"Failed to parse connection state for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            # Return None for corrupted data
            return None

    async def update_connection_state(self, connection_state: ConnectionState) -> None:
        """
        Update existing connection state in Redis.

        Args:
            connection_state: Updated connection state

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            await self._store_connection_state(connection_state)

            logger.debug(
                f"Updated connection state for {connection_state.connection_id}",
                extra={
                    "connection_id": connection_state.connection_id,
                    "health_status": connection_state.health_status.value,
                    "last_event_id": connection_state.last_event_id
                }
            )

        except redis.RedisError as e:
            logger.error(
                f"Failed to update connection state for {connection_state.connection_id}: {e}",
                extra={
                    "connection_id": connection_state.connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def update_last_activity(self, connection_id: str) -> None:
        """
        Update last activity timestamp for a connection.

        Args:
            connection_id: Connection identifier

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            key = self._get_connection_key(connection_id)

            # Update only the last_activity field
            await redis_client.hset(
                key,
                "last_activity",
                datetime.utcnow().isoformat()
            )

        except redis.RedisError as e:
            logger.error(
                f"Failed to update last activity for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def increment_error_count(self, connection_id: str) -> int:
        """
        Increment error count for a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            New error count

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            key = self._get_connection_key(connection_id)

            # Increment error count atomically
            new_count = await redis_client.hincrby(key, "error_count", 1)

            logger.warning(
                f"Incremented error count for {connection_id} to {new_count}",
                extra={
                    "connection_id": connection_id,
                    "error_count": new_count
                }
            )

            return new_count

        except redis.RedisError as e:
            logger.error(
                f"Failed to increment error count for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def increment_reconnection_count(self, connection_id: str) -> int:
        """
        Increment reconnection count for a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            New reconnection count

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            key = self._get_connection_key(connection_id)

            # Increment reconnection count atomically
            new_count = await redis_client.hincrby(key, "reconnection_count", 1)

            logger.info(
                f"Incremented reconnection count for {connection_id} to {new_count}",
                extra={
                    "connection_id": connection_id,
                    "reconnection_count": new_count
                }
            )

            return new_count

        except redis.RedisError as e:
            logger.error(
                f"Failed to increment reconnection count for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def delete_connection_state(self, connection_id: str) -> bool:
        """
        Delete connection state from Redis.

        Args:
            connection_id: Connection identifier

        Returns:
            True if connection was deleted, False if it didn't exist

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            key = self._get_connection_key(connection_id)

            # Use pipeline for atomic operations
            async with redis_client.pipeline() as pipe:
                await pipe.delete(key)
                await pipe.srem(self.connection_set_key, connection_id)
                results = await pipe.execute()

            deleted = results[0] > 0

            if deleted:
                logger.info(
                    f"Deleted connection state for {connection_id}",
                    extra={"connection_id": connection_id}
                )

            return deleted

        except redis.RedisError as e:
            logger.error(
                f"Failed to delete connection state for {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def get_all_active_connections(self) -> List[str]:
        """
        Get list of all active connection IDs.

        Returns:
            List of active connection IDs

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            redis_client = await self._get_redis_client()
            connection_ids = await redis_client.smembers(self.connection_set_key)
            return list(connection_ids)

        except redis.RedisError as e:
            logger.error(
                f"Failed to get active connections: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def get_connections_by_user(self, user_id: str) -> List[ConnectionState]:
        """
        Get all connections for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of ConnectionState objects for the user

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            connection_ids = await self.get_all_active_connections()
            user_connections = []

            for connection_id in connection_ids:
                connection_state = await self.get_connection_state(connection_id)
                if connection_state and connection_state.user_id == user_id:
                    user_connections.append(connection_state)

            return user_connections

        except redis.RedisError as e:
            logger.error(
                f"Failed to get connections for user {user_id}: {e}",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def get_stale_connections(self, timeout_seconds: int = 300) -> List[str]:
        """
        Get connections that haven't been active within the timeout period.

        Args:
            timeout_seconds: Timeout in seconds (default: 5 minutes)

        Returns:
            List of stale connection IDs

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            connection_ids = await self.get_all_active_connections()
            stale_connections = []
            cutoff_time = datetime.utcnow().timestamp() - timeout_seconds

            for connection_id in connection_ids:
                connection_state = await self.get_connection_state(connection_id)
                if connection_state:
                    last_activity_timestamp = connection_state.last_activity.timestamp()
                    if last_activity_timestamp < cutoff_time:
                        stale_connections.append(connection_id)

            return stale_connections

        except redis.RedisError as e:
            logger.error(
                f"Failed to get stale connections: {e}",
                extra={
                    "timeout_seconds": timeout_seconds,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

    async def _store_connection_state(self, connection_state: ConnectionState) -> None:
        """
        Store connection state in Redis using hash and set operations.

        Args:
            connection_state: Connection state to store

        Raises:
            redis.RedisError: If Redis operation fails
        """
        redis_client = await self._get_redis_client()
        key = self._get_connection_key(connection_state.connection_id)

        # Use pipeline for atomic operations
        async with redis_client.pipeline() as pipe:
            # Store connection data as hash
            await pipe.hset(key, mapping=connection_state.to_dict())
            # Add connection ID to active connections set
            await pipe.sadd(self.connection_set_key, connection_state.connection_id)
            # Set expiration for connection data (24 hours)
            await pipe.expire(key, 86400)
            await pipe.execute()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
