"""
WebSocket Connection Health Monitoring

This module provides health monitoring for websocket connections with
configurable intervals, timeout detection, and automatic cleanup.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from openhands.core.logger import openhands_logger as logger
from openhands.server.websocket.connection_state import (
    ConnectionState,
    ConnectionStateManager,
    HealthStatus,
)


class HealthCheckConfig:
    """Configuration for health monitoring."""

    def __init__(
        self,
        check_interval_seconds: int = 30,
        connection_timeout_seconds: int = 300,
        max_consecutive_failures: int = 3,
        cleanup_stale_connections: bool = True,
        stale_connection_threshold_seconds: int = 600,
    ):
        """
        Initialize health check configuration.

        Args:
            check_interval_seconds: Interval between health checks (default: 30s)
            connection_timeout_seconds: Timeout for connection health (default: 5 minutes)
            max_consecutive_failures: Max failures before marking unhealthy (default: 3)
            cleanup_stale_connections: Whether to automatically cleanup stale connections
            stale_connection_threshold_seconds: Threshold for stale connections (default: 10 minutes)
        """
        self.check_interval_seconds = check_interval_seconds
        self.connection_timeout_seconds = connection_timeout_seconds
        self.max_consecutive_failures = max_consecutive_failures
        self.cleanup_stale_connections = cleanup_stale_connections
        self.stale_connection_threshold_seconds = stale_connection_threshold_seconds


class ConnectionHealthMonitor:
    """Monitors websocket connection health and performs automatic cleanup."""

    def __init__(
        self,
        connection_state_manager: ConnectionStateManager,
        config: Optional[HealthCheckConfig] = None,
    ):
        """
        Initialize connection health monitor.

        Args:
            connection_state_manager: Connection state manager instance
            config: Health check configuration (uses defaults if None)
        """
        self.connection_state_manager = connection_state_manager
        self.config = config or HealthCheckConfig()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._consecutive_failures: Dict[str, int] = {}

    async def start_monitoring(self) -> None:
        """Start the health monitoring background task."""
        if self._is_running:
            logger.warning("Health monitoring is already running")
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(
            "Started connection health monitoring",
            extra={
                "check_interval": self.config.check_interval_seconds,
                "connection_timeout": self.config.connection_timeout_seconds,
                "max_failures": self.config.max_consecutive_failures,
            }
        )

    async def stop_monitoring(self) -> None:
        """Stop the health monitoring background task."""
        if not self._is_running:
            return

        self._is_running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        logger.info("Stopped connection health monitoring")

    async def check_connection_health(self, connection_id: str) -> HealthStatus:
        """
        Check the health of a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Current health status of the connection
        """
        try:
            connection_state = await self.connection_state_manager.get_connection_state(connection_id)
            if not connection_state:
                logger.debug(f"Connection {connection_id} not found in state manager")
                return HealthStatus.DISCONNECTED

            now = datetime.utcnow()
            time_since_activity = now - connection_state.last_activity

            # Check if connection has timed out
            if time_since_activity.total_seconds() > self.config.connection_timeout_seconds:
                new_status = HealthStatus.UNHEALTHY
                logger.warning(
                    f"Connection {connection_id} timed out",
                    extra={
                        "connection_id": connection_id,
                        "last_activity": connection_state.last_activity.isoformat(),
                        "timeout_seconds": self.config.connection_timeout_seconds,
                        "time_since_activity": time_since_activity.total_seconds(),
                    }
                )
            else:
                # Check error count to determine health status
                if connection_state.error_count >= self.config.max_consecutive_failures:
                    new_status = HealthStatus.DEGRADED
                elif connection_state.error_count > 0:
                    new_status = HealthStatus.DEGRADED
                else:
                    new_status = HealthStatus.HEALTHY

            # Update health status if it changed
            if new_status != connection_state.health_status:
                connection_state.health_status = new_status
                await self.connection_state_manager.update_connection_state(connection_state)

                logger.info(
                    f"Updated connection {connection_id} health status to {new_status.value}",
                    extra={
                        "connection_id": connection_id,
                        "old_status": connection_state.health_status.value,
                        "new_status": new_status.value,
                        "error_count": connection_state.error_count,
                    }
                )

            return new_status

        except Exception as e:
            logger.error(
                f"Failed to check health for connection {connection_id}: {e}",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return HealthStatus.UNHEALTHY

    async def check_all_connections_health(self) -> Dict[str, HealthStatus]:
        """
        Check health of all active connections.

        Returns:
            Dictionary mapping connection IDs to their health status
        """
        try:
            connection_ids = await self.connection_state_manager.get_all_active_connections()
            health_results = {}

            # Check health for each connection
            for connection_id in connection_ids:
                health_status = await self.check_connection_health(connection_id)
                health_results[connection_id] = health_status

            # Log summary
            healthy_count = sum(1 for status in health_results.values() if status == HealthStatus.HEALTHY)
            degraded_count = sum(1 for status in health_results.values() if status == HealthStatus.DEGRADED)
            unhealthy_count = sum(1 for status in health_results.values() if status == HealthStatus.UNHEALTHY)

            logger.debug(
                f"Health check completed for {len(connection_ids)} connections",
                extra={
                    "total_connections": len(connection_ids),
                    "healthy": healthy_count,
                    "degraded": degraded_count,
                    "unhealthy": unhealthy_count,
                }
            )

            return health_results

        except Exception as e:
            logger.error(
                f"Failed to check health for all connections: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return {}

    async def cleanup_unhealthy_connections(self) -> List[str]:
        """
        Clean up connections that are unhealthy or timed out.

        Returns:
            List of connection IDs that were cleaned up
        """
        cleaned_up = []

        try:
            # Get all connections and check their health
            health_results = await self.check_all_connections_health()

            for connection_id, health_status in health_results.items():
                if health_status == HealthStatus.UNHEALTHY:
                    try:
                        # Remove from connection state
                        await self.connection_state_manager.delete_connection_state(connection_id)
                        cleaned_up.append(connection_id)

                        logger.info(
                            f"Cleaned up unhealthy connection {connection_id}",
                            extra={"connection_id": connection_id}
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to cleanup connection {connection_id}: {e}",
                            extra={
                                "connection_id": connection_id,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            }
                        )

            if cleaned_up:
                logger.info(
                    f"Cleaned up {len(cleaned_up)} unhealthy connections",
                    extra={
                        "cleaned_up_count": len(cleaned_up),
                        "connection_ids": cleaned_up,
                    }
                )

            return cleaned_up

        except Exception as e:
            logger.error(
                f"Failed to cleanup unhealthy connections: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return []

    async def cleanup_stale_connections(self) -> List[str]:
        """
        Clean up connections that haven't been active for a long time.

        Returns:
            List of connection IDs that were cleaned up
        """
        if not self.config.cleanup_stale_connections:
            return []

        cleaned_up = []

        try:
            stale_connections = await self.connection_state_manager.get_stale_connections(
                timeout_seconds=self.config.stale_connection_threshold_seconds
            )

            for connection_id in stale_connections:
                try:
                    await self.connection_state_manager.delete_connection_state(connection_id)
                    cleaned_up.append(connection_id)

                    logger.info(
                        f"Cleaned up stale connection {connection_id}",
                        extra={"connection_id": connection_id}
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to cleanup stale connection {connection_id}: {e}",
                        extra={
                            "connection_id": connection_id,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    )

            if cleaned_up:
                logger.info(
                    f"Cleaned up {len(cleaned_up)} stale connections",
                    extra={
                        "cleaned_up_count": len(cleaned_up),
                        "connection_ids": cleaned_up,
                    }
                )

            return cleaned_up

        except Exception as e:
            logger.error(
                f"Failed to cleanup stale connections: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return []

    async def get_connection_metrics(self) -> Dict[str, int]:
        """
        Get connection health metrics.

        Returns:
            Dictionary with connection health metrics
        """
        try:
            health_results = await self.check_all_connections_health()

            metrics = {
                "total_connections": len(health_results),
                "healthy_connections": sum(1 for status in health_results.values() if status == HealthStatus.HEALTHY),
                "degraded_connections": sum(1 for status in health_results.values() if status == HealthStatus.DEGRADED),
                "unhealthy_connections": sum(1 for status in health_results.values() if status == HealthStatus.UNHEALTHY),
                "disconnected_connections": sum(1 for status in health_results.values() if status == HealthStatus.DISCONNECTED),
            }

            return metrics

        except Exception as e:
            logger.error(
                f"Failed to get connection metrics: {e}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return {
                "total_connections": 0,
                "healthy_connections": 0,
                "degraded_connections": 0,
                "unhealthy_connections": 0,
                "disconnected_connections": 0,
            }

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs in the background."""
        logger.info("Starting connection health monitoring loop")

        while self._is_running:
            try:
                start_time = time.time()

                # Check health of all connections
                await self.check_all_connections_health()

                # Cleanup unhealthy connections
                await self.cleanup_unhealthy_connections()

                # Cleanup stale connections
                await self.cleanup_stale_connections()

                # Log monitoring cycle metrics
                cycle_time = time.time() - start_time
                logger.debug(
                    f"Health monitoring cycle completed in {cycle_time:.2f}s",
                    extra={"cycle_time_seconds": cycle_time}
                )

                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval_seconds)

            except asyncio.CancelledError:
                logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(
                    f"Error in health monitoring loop: {e}",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(min(self.config.check_interval_seconds, 10))

        logger.info("Connection health monitoring loop stopped")

    def is_running(self) -> bool:
        """Check if the health monitor is currently running."""
        return self._is_running
