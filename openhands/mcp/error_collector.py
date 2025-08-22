"""MCP Error Collector for capturing and storing MCP-related errors during startup."""

import threading
import time
from dataclasses import dataclass


@dataclass
class MCPError:
    """Represents an MCP-related error."""

    timestamp: float
    server_name: str
    server_type: str  # 'stdio', 'sse', 'shttp'
    error_message: str
    exception_details: str | None = None


class MCPErrorCollector:
    """Thread-safe collector for MCP errors during startup."""

    def __init__(self):
        self._errors: list[MCPError] = []
        self._lock = threading.Lock()
        self._collection_enabled = True

    def add_error(
        self,
        server_name: str,
        server_type: str,
        error_message: str,
        exception_details: str | None = None,
    ) -> None:
        """Add an MCP error to the collection."""
        if not self._collection_enabled:
            return

        with self._lock:
            error = MCPError(
                timestamp=time.time(),
                server_name=server_name,
                server_type=server_type,
                error_message=error_message,
                exception_details=exception_details,
            )
            self._errors.append(error)

    def get_errors(self) -> list[MCPError]:
        """Get a copy of all collected errors."""
        with self._lock:
            return self._errors.copy()

    def has_errors(self) -> bool:
        """Check if there are any collected errors."""
        with self._lock:
            return len(self._errors) > 0

    def clear_errors(self) -> None:
        """Clear all collected errors."""
        with self._lock:
            self._errors.clear()

    def disable_collection(self) -> None:
        """Disable error collection (useful after startup)."""
        self._collection_enabled = False

    def enable_collection(self) -> None:
        """Enable error collection."""
        self._collection_enabled = True

    def get_error_count(self) -> int:
        """Get the number of collected errors."""
        with self._lock:
            return len(self._errors)


# Global instance for collecting MCP errors
mcp_error_collector = MCPErrorCollector()
