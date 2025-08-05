"""
WebSocket Connection Resource Management

This module provides resource management for websocket connections including
graceful termination, resource usage tracking, and optimization.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from openhands.core.logger import openhands_logger as logger
from openhands.server.websocket.connection_state import (
    ConnectionState,
    ConnectionStateManager,
    HealthStatus,
)


@dataclass
class ResourceUsage:
    """Resource usage metrics for a connection."""

    connection_id: str
    memory_usage_bytes: int
    cpu_usage_percent: float
    message_count: int
    error_count: int
    last_updated: datetime

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for logging/storage."""
        return {
            "connection_id": self.connection_id,
            "memory_usage_bytes": self.memory_usage_bytes,
            "cpu_usage_percent": self.cpu_usage_percent,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class CleanupConfig:
    """Configuration for connection cleanup and resource management."""

    def __init__(
        self,
        max_connections_per_user: int = 10,
        max_total_connections: int = 1000,
        memory_threshold_mb: int = 100,
        cpu_threshold_percent: float = 80.0,
        cleanup_interval_seconds: int = 60,
        graceful_shutdown_timeout_seconds: int = 30,
        force_cleanup_after_seconds: int = 300,
    ):
        """
        Initialize cleanup configuration.

        Args:
            max_connections_per_user: Maximum connections per user
            max_total_connections: Maximum total connections
            memory_threshold_mb: Memory usage threshold in MB
            cpu_threshold_percent: CPU usage threshold percentage
            cleanup_interval_seconds: Interval between cleanup cycles
            graceful_shutdown_timeout_seconds: Timeout for graceful shutdown
            force_cleanup_after_seconds: Force cleanup after this time
        """
        self.max_connections_per_user = max_connections_per_user
        self.max_total_connections = max_total_connections
        self.memory_threshold_mb = memory_threshold_mb
        self.cpu_threshold_percent = cpu_threshold_percent
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.graceful_shutdown_timeout_seconds = graceful_shutdown_timeout_seconds
        self.force_cleanup_after_seconds = force_cleanup_after_seconds


class ConnectionResourceManager:
    """Manages websocket connection resources and performs cleanup."""

    def __init__(
        self,
        connection_state_manager: ConnectionStateManager,
        config: Optional[CleanupConfig] = None,
    ):
        """
        Initialize connection resource manager.

        Args:
            connection_state_manager: Connection state manager instance
            config: Cleanup configuration (uses defaults if None)
        """
        self.connection_state_manager = connection_state_manager
        self.config = config or CleanupConfig()
        self._resource_usage: Dict[str, ResourceUsage] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._shutdown_connections: Set[str] = set()

    async def start_resource_management(self) -> None:
        """Start the resource management background task."""
        if self._is_running:
            logger.warning("Resource management is already running")
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(
            "Started connection resource management",
            extra={
                "cleanup_interval": self.config.cleanup_interval_seconds,
                "max_connections_per_user": self.config.max_connections_per_user,
                "max_total_connections": self.config.max_total_connections,
                "memory_threshold_mb": self.config.memory_threshold_mb,
            }
        )

    async def stop_resource_management(self) -> None:
        """Stop the resource management background task."""
        if not self._is_running:
            return

        self._is_running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        logger.info("Stopped connection resource management")

    async def track_resource_usage(
        self,
        connection_id: str,
        memory_usage_bytes: int = 0,
        cpu_usage_percent: float = 0.0,
        message_count: int = 0,
        error_count: int = 0,
    ) -> None:
        """
        Track resource usage for a connection.

        Args:
            connection_id: Connection identifier
            memory_usage_bytes: Memory usage in bytes
            cpu_usage_percent: CPU usage percentage
            message_count: Number of messages processed
            error_count: Number of errors encountered
        """
        try:
            self._resource_usage[connection_id] = ResourceUsage(
                connection_id=connection_id,
                memory_usage_bytes=memory_usage_bytes,
                cpu_usage_percent=cpu_usage_percent,
                message_count=message_count,
                error_count=error_count,
                last_updated=datetime.utcnow(),
            )

            logger.debug(
                f"Updated resource usage for connection {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "memory_mb": memory_usage_bytes / (1024 * 1024),
                    "cpu_percent": cpu_usage_percent,
                    "message_count": message_count,
                    "error_count": error_count,
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to track resource usage for connection {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

    async def get_resource_usage(self, connection_id: str) -> Optional[ResourceUsage]:
        """
        Get resource usage for a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            ResourceUsage if found, None otherwise
        """
        return self._resource_usage.get(connection_id)

    async def get_all_resource_usage(self) -> Dict[str, ResourceUsage]:
        """
        Get resource usage for all tracked connections.

        Returns:
            Dictionary mapping connection IDs to ResourceUsage
        """
        return self._resource_usage.copy()

    async def initiate_graceful_shutdown(self, connection_id: str, reason: str = "cleanup") -> bool:
        """
        Initiate graceful shutdown for a connection.

        Args:
            connection_id: Connection identifier
            reason: Reason for shutdown

        Returns:
            True if shutdown was initiated, False otherwise
        """
        try:
            # Mark connection for shutdown
            self._shutdown_connections.add(connection_id)

            # Update connection state to indicate shutdown
            connection_state = await self.connection_state_manager.get_connection_state(connection_id)
            if connection_state:
                connection_state.health_status = HealthStatus.DISCONNECTED
                await self.connection_state_manager.update_connection_state(connection_state)

            logger.info(
                f"Initiated graceful shutdown for connection {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "reason": reason,
                }
            )

            # Schedule force cleanup after timeout
            asyncio.create_task(self._force_cleanup_after_timeout(connection_id))

            return True

        except Exception as e:
            logger.error(
                f"Failed to initiate graceful shutdown for connection {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "reason": reason,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return False

    async def force_cleanup_connection(self, connection_id: str, reason: str = "force_cleanup") -> bool:
        """
        Force cleanup of a connection and its resources.

        Args:
            connection_id: Connection identifier
            reason: Reason for cleanup

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            # Remove from resource tracking
            self._resource_usage.pop(connection_id, None)

            # Remove from shutdown tracking
            self._shutdown_connections.discard(connection_id)

            # Remove from connection state
            await self.connection_state_manager.delete_connection_state(connection_id)

            logger.info(
                f"Force cleaned up connection {connection_id}",
                extra={
                    "connection_id": connection_id,
                    "reason": reason,
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to force cleanup connection {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "reason": reason,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return False

    async def cleanup_connections_by_user_limit(self) -> List[str]:
        """
        Clean up connections that exceed per-user limits.

        Returns:
            List of connection IDs that were cleaned up
        """
        cleaned_up = []

        try:
            # Get all active connections
            connection_ids = await self.connection_state_manager.get_all_active_connections()

            # Group connections by user
            user_connections: Dict[str, List[str]] = {}
            for connection_id in connection_ids:
                connection_state = await self.connection_state_manager.get_connection_state(connection_id)
                if connection_state:
                    user_id = connection_state.user_id
                    if user_id not in user_connections:
                        user_connections[user_id] = []
                    user_connections[user_id].append(connection_id)

            # Check each user's connection count
            for user_id, connections in user_connections.items():
                if len(connections) > self.config.max_connections_per_user:
                    # Sort by last activity (oldest first) and clean up excess
                    connections_with_activity = []
                    for conn_id in connections:
                        conn_state = await self.connection_state_manager.get_connection_state(conn_id)
                        if conn_state:
                            connections_with_activity.append((conn_id, conn_state.last_activity))

                    # Sort by last activity (oldest first)
                    connections_with_activity.sort(key=lambda x: x[1])

                    # Clean up excess connections
                    excess_count = len(connections) - self.config.max_connections_per_user
                    for i in range(excess_count):
                        conn_id = connections_with_activity[i][0]
                        if await self.initiate_graceful_shutdown(conn_id, "user_limit_exceeded"):
                            cleaned_up.append(conn_id)

                    logger.info(
                        f"Cleaned up {excess_count} excess connections for user {user_id}",
                        extra={
                            "user_id": user_id,
                            "total_connections": len(connections),
                            "max_allowed": self.config.max_connections_per_user,
                            "cleaned_up": excess_count,
                        }
                    )

            return cleaned_up

        except Exception as e:
            logger.error(
                f"Failed to cleanup connections by user limit: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return []

    async def cleanup_connections_by_resource_usage(self) -> List[str]:
        """
        Clean up connections that exceed resource usage thresholds.

        Returns:
            List of connection IDs that were cleaned up
        """
        cleaned_up = []

        try:
            memory_threshold_bytes = self.config.memory_threshold_mb * 1024 * 1024

            for connection_id, usage in self._resource_usage.items():
                should_cleanup = False
                reason = ""

                # Check memory usage
                if usage.memory_usage_bytes > memory_threshold_bytes:
                    should_cleanup = True
                    reason = f"memory_usage_exceeded_{usage.memory_usage_bytes / (1024 * 1024):.1f}MB"

                # Check CPU usage
                elif usage.cpu_usage_percent > self.config.cpu_threshold_percent:
                    should_cleanup = True
                    reason = f"cpu_usage_exceeded_{usage.cpu_usage_percent:.1f}%"

                if should_cleanup:
                    if await self.initiate_graceful_shutdown(connection_id, reason):
                        cleaned_up.append(connection_id)

                        logger.warning(
                            f"Cleaned up connection {connection_id} due to resource usage",
                            extra={
                                "connection_id": connection_id,
                                "reason": reason,
                                "memory_mb": usage.memory_usage_bytes / (1024 * 1024),
                                "cpu_percent": usage.cpu_usage_percent,
                            }
                        )

            return cleaned_up

        except Exception as e:
            logger.error(
                f"Failed to cleanup connections by resource usage: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return []

    async def cleanup_stale_resource_tracking(self) -> int:
        """
        Clean up stale resource usage tracking entries.

        Returns:
            Number of entries cleaned up
        """
        cleaned_up = 0

        try:
            # Get active connections
            active_connections = set(await self.connection_state_manager.get_all_active_connections())

            # Remove tracking for inactive connections
            stale_connections = []
            for connection_id in self._resource_usage.keys():
                if connection_id not in active_connections:
                    stale_connections.append(connection_id)

            for connection_id in stale_connections:
                del self._resource_usage[connection_id]
                cleaned_up += 1

            if cleaned_up > 0:
                logger.info(
                    f"Cleaned up {cleaned_up} stale resource tracking entries",
                    extra={"cleaned_up_count": cleaned_up}
                )

            return cleaned_up

        except Exception as e:
            logger.error(
                f"Failed to cleanup stale resource tracking: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return 0

    async def get_resource_metrics(self) -> Dict[str, any]:
        """
        Get overall resource usage metrics.

        Returns:
            Dictionary with resource metrics
        """
        try:
            total_connections = len(self._resource_usage)
            total_memory_bytes = sum(usage.memory_usage_bytes for usage in self._resource_usage.values())
            avg_cpu_percent = (
                sum(usage.cpu_usage_percent for usage in self._resource_usage.values()) / total_connections
                if total_connections > 0 else 0.0
            )
            total_messages = sum(usage.message_count for usage in self._resource_usage.values())
            total_errors = sum(usage.error_count for usage in self._resource_usage.values())

            # Count connections exceeding thresholds
            memory_threshold_bytes = self.config.memory_threshold_mb * 1024 * 1024
            high_memory_connections = sum(
                1 for usage in self._resource_usage.values()
                if usage.memory_usage_bytes > memory_threshold_bytes
            )
            high_cpu_connections = sum(
                1 for usage in self._resource_usage.values()
                if usage.cpu_usage_percent > self.config.cpu_threshold_percent
            )

            return {
                "total_connections": total_connections,
                "total_memory_mb": total_memory_bytes / (1024 * 1024),
                "average_cpu_percent": avg_cpu_percent,
                "total_messages": total_messages,
                "total_errors": total_errors,
                "high_memory_connections": high_memory_connections,
                "high_cpu_connections": high_cpu_connections,
                "shutdown_pending_connections": len(self._shutdown_connections),
            }

        except Exception as e:
            logger.error(
                f"Failed to get resource metrics: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return {
                "total_connections": 0,
                "total_memory_mb": 0.0,
                "average_cpu_percent": 0.0,
                "total_messages": 0,
                "total_errors": 0,
                "high_memory_connections": 0,
                "high_cpu_connections": 0,
                "shutdown_pending_connections": 0,
            }

    async def _force_cleanup_after_timeout(self, connection_id: str) -> None:
        """Force cleanup a connection after graceful shutdown timeout."""
        try:
            await asyncio.sleep(self.config.graceful_shutdown_timeout_seconds)

            # Check if connection is still in shutdown state
            if connection_id in self._shutdown_connections:
                await self.force_cleanup_connection(connection_id, "graceful_shutdown_timeout")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(
                f"Error in force cleanup timeout for connection {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

    async def _cleanup_loop(self) -> None:
        """Main cleanup loop that runs in the background."""
        logger.info("Starting connection resource management loop")

        while self._is_running:
            try:
                start_time = time.time()

                # Cleanup by user limits
                await self.cleanup_connections_by_user_limit()

                # Cleanup by resource usage
                await self.cleanup_connections_by_resource_usage()

                # Cleanup stale resource tracking
                await self.cleanup_stale_resource_tracking()

                # Log cleanup cycle metrics
                cycle_time = time.time() - start_time
                metrics = await self.get_resource_metrics()

                logger.debug(
                    f"Resource management cycle completed in {cycle_time:.2f}s",
                    extra={
                        "cycle_time_seconds": cycle_time,
                        **metrics,
                    }
                )

                # Wait for next cleanup interval
                await asyncio.sleep(self.config.cleanup_interval_seconds)

            except asyncio.CancelledError:
                logger.info("Resource management loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"Error in resource management loop: {e}",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(min(self.config.cleanup_interval_seconds, 10))

        logger.info("Connection resource management loop stopped")

    def is_running(self) -> bool:
        """Check if the resource manager is currently running."""
        return self._is_running
