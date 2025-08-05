"""
WebSocket Connection Monitor Utility

This module provides utilities to monitor and inspect websocket connection states.
"""

import asyncio
import os
from typing import Dict, List, Optional

from openhands.core.logger import openhands_logger as logger
from openhands.server.websocket.connection_state import (
    ConnectionState,
    ConnectionStateManager,
    HealthStatus,
)


class ConnectionMonitor:
    """Utility class for monitoring websocket connections."""

    def __init__(self):
        """Initialize connection monitor with Redis configuration."""
        redis_host = os.environ.get('REDIS_HOST')
        redis_password = os.environ.get('REDIS_PASSWORD')

        if redis_host:
            redis_url = f'redis://{redis_host}'
            self.connection_state_manager = ConnectionStateManager(redis_url, redis_password)
        else:
            # Fallback to localhost Redis for development
            self.connection_state_manager = ConnectionStateManager()

    async def get_all_connections(self) -> List[ConnectionState]:
        """
        Get all active connections.

        Returns:
            List of ConnectionState objects
        """
        try:
            connection_ids = await self.connection_state_manager.get_all_active_connections()
            connections = []

            for connection_id in connection_ids:
                connection_state = await self.connection_state_manager.get_connection_state(connection_id)
                if connection_state:
                    connections.append(connection_state)

            return connections

        except Exception as e:
            logger.error(f"Failed to get all connections: {e}")
            return []

    async def get_connections_by_user(self, user_id: str) -> List[ConnectionState]:
        """
        Get all connections for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of ConnectionState objects for the user
        """
        try:
            return await self.connection_state_manager.get_connections_by_user(user_id)
        except Exception as e:
            logger.error(f"Failed to get connections for user {user_id}: {e}")
            return []

    async def get_connection_summary(self) -> Dict[str, any]:
        """
        Get a summary of all connections.

        Returns:
            Dictionary with connection summary statistics
        """
        try:
            connections = await self.get_all_connections()

            # Count by status
            status_counts = {}
            for status in HealthStatus:
                status_counts[status.value] = 0

            # Count by user
            user_counts = {}

            for conn in connections:
                # Count by status
                status_counts[conn.health_status.value] += 1

                # Count by user
                if conn.user_id not in user_counts:
                    user_counts[conn.user_id] = 0
                user_counts[conn.user_id] += 1

            return {
                "total_connections": len(connections),
                "status_breakdown": status_counts,
                "users_with_connections": len(user_counts),
                "connections_per_user": user_counts,
                "average_connections_per_user": len(connections) / len(user_counts) if user_counts else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get connection summary: {e}")
            return {
                "total_connections": 0,
                "status_breakdown": {},
                "users_with_connections": 0,
                "connections_per_user": {},
                "average_connections_per_user": 0,
            }

    async def print_connection_summary(self) -> None:
        """Print a formatted connection summary to the console."""
        summary = await self.get_connection_summary()

        print("\n=== WebSocket Connection Summary ===")
        print(f"Total Connections: {summary['total_connections']}")
        print(f"Users with Connections: {summary['users_with_connections']}")
        print(f"Average Connections per User: {summary['average_connections_per_user']:.1f}")

        print("\nStatus Breakdown:")
        for status, count in summary['status_breakdown'].items():
            print(f"  {status.upper()}: {count}")

        if summary['connections_per_user']:
            print("\nConnections per User:")
            for user_id, count in summary['connections_per_user'].items():
                print(f"  {user_id}: {count}")

        print("=" * 37)

    async def print_detailed_connections(self) -> None:
        """Print detailed information about all connections."""
        connections = await self.get_all_connections()

        print("\n=== Detailed Connection Information ===")

        if not connections:
            print("No active connections found.")
            print("=" * 40)
            return

        for i, conn in enumerate(connections, 1):
            print(f"\nConnection {i}:")
            print(f"  ID: {conn.connection_id}")
            print(f"  User: {conn.user_id}")
            print(f"  Conversation: {conn.conversation_id}")
            print(f"  Status: {conn.health_status.value}")
            print(f"  Connected: {conn.connected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  Last Activity: {conn.last_activity.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  Last Event ID: {conn.last_event_id}")
            print(f"  Reconnections: {conn.reconnection_count}")
            print(f"  Errors: {conn.error_count}")

            if conn.client_info:
                print(f"  Client Info:")
                for key, value in conn.client_info.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"    {key}: {value}")

        print("=" * 40)

    async def cleanup_stale_connections(self, timeout_seconds: int = 300) -> int:
        """
        Clean up connections that haven't been active for the specified time.

        Args:
            timeout_seconds: Timeout in seconds (default: 5 minutes)

        Returns:
            Number of connections cleaned up
        """
        try:
            stale_connections = await self.connection_state_manager.get_stale_connections(timeout_seconds)

            cleaned_up = 0
            for connection_id in stale_connections:
                try:
                    await self.connection_state_manager.delete_connection_state(connection_id)
                    cleaned_up += 1
                    logger.info(f"Cleaned up stale connection: {connection_id}")
                except Exception as e:
                    logger.error(f"Failed to clean up connection {connection_id}: {e}")

            if cleaned_up > 0:
                print(f"Cleaned up {cleaned_up} stale connections (inactive for >{timeout_seconds}s)")
            else:
                print("No stale connections found to clean up")

            return cleaned_up

        except Exception as e:
            logger.error(f"Failed to cleanup stale connections: {e}")
            return 0


async def main():
    """Main function for running the connection monitor as a standalone script."""
    import sys

    monitor = ConnectionMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "summary":
            await monitor.print_connection_summary()
        elif command == "detailed" or command == "detail":
            await monitor.print_detailed_connections()
        elif command == "cleanup":
            timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            await monitor.cleanup_stale_connections(timeout)
        else:
            print("Usage: python -m openhands.server.websocket.connection_monitor [summary|detailed|cleanup [timeout_seconds]]")
    else:
        # Default: show summary
        await monitor.print_connection_summary()


if __name__ == "__main__":
    asyncio.run(main())
