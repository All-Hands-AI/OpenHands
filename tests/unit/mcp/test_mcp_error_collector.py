"""Tests for MCP Error Collector functionality."""

import time

from openhands.mcp.error_collector import (
    MCPError,
    MCPErrorCollector,
    mcp_error_collector,
)


class TestMCPError:
    """Test MCPError dataclass."""

    def test_mcp_error_creation(self):
        """Test creating an MCP error."""
        timestamp = time.time()
        error = MCPError(
            timestamp=timestamp,
            server_name="test-server",
            server_type="stdio",
            error_message="Connection failed",
            exception_details="Socket timeout",
        )

        assert error.timestamp == timestamp
        assert error.server_name == "test-server"
        assert error.server_type == "stdio"
        assert error.error_message == "Connection failed"
        assert error.exception_details == "Socket timeout"

    def test_mcp_error_creation_without_exception_details(self):
        """Test creating an MCP error without exception details."""
        timestamp = time.time()
        error = MCPError(
            timestamp=timestamp,
            server_name="test-server",
            server_type="sse",
            error_message="Server unreachable",
        )

        assert error.timestamp == timestamp
        assert error.server_name == "test-server"
        assert error.server_type == "sse"
        assert error.error_message == "Server unreachable"
        assert error.exception_details is None


class TestMCPErrorCollector:
    """Test MCPErrorCollector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = MCPErrorCollector()

    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector._errors == []
        assert self.collector._collection_enabled is True

    def test_add_error(self):
        """Test adding an error to the collector."""
        self.collector.add_error(
            server_name="test-server",
            server_type="stdio",
            error_message="Connection failed",
            exception_details="Socket timeout",
        )

        errors = self.collector.get_errors()
        assert len(errors) == 1
        assert errors[0].server_name == "test-server"
        assert errors[0].server_type == "stdio"
        assert errors[0].error_message == "Connection failed"
        assert errors[0].exception_details == "Socket timeout"
        assert errors[0].timestamp > 0

    def test_add_multiple_errors(self):
        """Test adding multiple errors."""
        self.collector.add_error("server1", "stdio", "Error 1")
        self.collector.add_error("server2", "sse", "Error 2")
        self.collector.add_error("server3", "shttp", "Error 3")

        errors = self.collector.get_errors()
        assert len(errors) == 3
        assert errors[0].server_name == "server1"
        assert errors[1].server_name == "server2"
        assert errors[2].server_name == "server3"

    def test_has_errors(self):
        """Test has_errors method."""
        assert not self.collector.has_errors()

        self.collector.add_error("server1", "stdio", "Error 1")
        assert self.collector.has_errors()

        self.collector.clear_errors()
        assert not self.collector.has_errors()

    def test_clear_errors(self):
        """Test clearing errors."""
        self.collector.add_error("server1", "stdio", "Error 1")
        self.collector.add_error("server2", "sse", "Error 2")

        assert len(self.collector.get_errors()) == 2

        self.collector.clear_errors()
        assert len(self.collector.get_errors()) == 0
        assert not self.collector.has_errors()

    def test_enable_disable_collection(self):
        """Test enabling and disabling error collection."""
        self.collector.add_error("server1", "stdio", "Error 1")
        assert len(self.collector.get_errors()) == 1

        # Disable collection
        self.collector.disable_collection()

        # Adding error should be ignored
        self.collector.add_error("server2", "sse", "Error 2")
        assert len(self.collector.get_errors()) == 1  # Still only 1 error

        # Re-enable collection
        self.collector.enable_collection()

        # Adding error should work again
        self.collector.add_error("server3", "shttp", "Error 3")
        assert len(self.collector.get_errors()) == 2


class TestGlobalMCPErrorCollector:
    """Test the global MCP error collector instance."""

    def setup_method(self):
        """Clear global collector before each test."""
        mcp_error_collector.clear_errors()
        mcp_error_collector.enable_collection()

    def teardown_method(self):
        """Clean up after each test."""
        mcp_error_collector.clear_errors()
        mcp_error_collector.enable_collection()

    def test_global_collector_exists(self):
        """Test that global collector instance exists."""
        assert mcp_error_collector is not None
        assert isinstance(mcp_error_collector, MCPErrorCollector)

    def test_global_collector_functionality(self):
        """Test basic functionality of global collector."""
        assert not mcp_error_collector.has_errors()

        mcp_error_collector.add_error("global-server", "stdio", "Global error")
        assert mcp_error_collector.has_errors()
        assert mcp_error_collector.get_error_count() == 1

        errors = mcp_error_collector.get_errors()
        assert len(errors) == 1
        assert errors[0].server_name == "global-server"
