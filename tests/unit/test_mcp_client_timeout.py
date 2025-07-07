import pytest
from httpx import ConnectError
from mcp import McpError

from openhands.core.config.mcp_config import MCPSSEServerConfig
from openhands.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_connect_sse_timeout():
    """Test that connect_http properly times out"""
    client = MCPClient()

    # Use a non-routable IP address from TEST-NET-1 range (192.0.2.0/24)
    # This ensures consistent timeout behavior across environments
    server = MCPSSEServerConfig(url='http://192.0.2.1:8080')

    # Test with a very short timeout
    with pytest.raises(McpError, match='Timed out'):
        await client.connect_http(server, timeout=0.001)


@pytest.mark.asyncio
async def test_connect_sse_invalid_url():
    """Test that connect_http hits error when server_url is invalid."""
    client = MCPClient()

    # Use a hostname that will definitely not resolve to test DNS resolution errors
    # This should cause a ConnectError rather than a timeout
    server = MCPSSEServerConfig(
        url='http://non-existent-domain-that-will-never-resolve.invalid'
    )

    # Test with larger timeout
    with pytest.raises(ConnectError):
        await client.connect_http(server, timeout=1)
