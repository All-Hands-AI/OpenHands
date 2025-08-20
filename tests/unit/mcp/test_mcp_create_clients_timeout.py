import asyncio

import pytest

from openhands.core.config.mcp_config import MCPSSEServerConfig
from openhands.mcp.client import MCPClient
from openhands.mcp.utils import create_mcp_clients


@pytest.mark.asyncio
async def test_create_mcp_clients_timeout_with_invalid_url():
    """Test that create_mcp_clients properly times out when given an invalid URL."""
    # Use a non-existent domain that should cause a connection timeout
    server = MCPSSEServerConfig(
        url='http://non-existent-domain-that-will-timeout.invalid'
    )

    # Temporarily modify the default timeout for the MCPClient.connect_http method
    original_connect_connect_http = MCPClient.connect_http

    # Create a wrapper that calls the original method but with a shorter timeout
    async def connect_http_with_short_timeout(self, server_url, timeout=30.0):
        return await original_connect_connect_http(self, server_url, timeout=0.5)

    try:
        # Replace the method with our wrapper
        MCPClient.connect_http = connect_http_with_short_timeout

        # Call create_mcp_clients with the invalid URL
        start_time = asyncio.get_event_loop().time()
        clients = await create_mcp_clients([server], [])
        end_time = asyncio.get_event_loop().time()

        # Verify that no clients were successfully connected
        assert len(clients) == 0

        # Verify that the operation completed in a reasonable time (less than 5 seconds)
        # This ensures the timeout is working properly
        assert end_time - start_time < 5.0, (
            'Operation took too long, timeout may not be working'
        )
    finally:
        # Restore the original method
        MCPClient.connect_http = original_connect_connect_http


@pytest.mark.asyncio
async def test_create_mcp_clients_with_unreachable_host():
    """Test that create_mcp_clients handles unreachable hosts properly."""
    # Use a URL with a valid format but pointing to a non-routable IP address
    # This IP is in the TEST-NET-1 range (192.0.2.0/24) reserved for documentation and examples
    unreachable_url = 'http://192.0.2.1:8080'

    # Temporarily modify the default timeout for the MCPClient.connect_http method
    original_connect_http = MCPClient.connect_http

    # Create a wrapper that calls the original method but with a shorter timeout
    async def connect_http_with_short_timeout(self, server_url, timeout=30.0):
        return await original_connect_http(self, server_url, timeout=1.0)

    try:
        # Replace the method with our wrapper
        MCPClient.connect_http = connect_http_with_short_timeout

        # Call create_mcp_clients with the unreachable URL
        start_time = asyncio.get_event_loop().time()
        clients = await create_mcp_clients([unreachable_url], [])
        end_time = asyncio.get_event_loop().time()

        # Verify that no clients were successfully connected
        assert len(clients) == 0

        # Verify that the operation completed in a reasonable time (less than 5 seconds)
        assert end_time - start_time < 5.0, (
            'Operation took too long, timeout may not be working'
        )
    finally:
        # Restore the original method
        MCPClient.connect_http = original_connect_http
