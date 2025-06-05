import pytest
from openhands.core.config.mcp_config import MCPSSEServerConfig
from openhands.mcp.client import MCPClient
from mcp import McpError

@pytest.mark.asyncio
async def test_connect_sse_timeout():
    """Test that connect_sse properly times out when server_url is invalid."""
    client = MCPClient()


    server = MCPSSEServerConfig(url='http://server1:8080')

    # Test with a very short timeout
    with pytest.raises(McpError, match='Timed out'):
        await client.connect_http(server, timeout=0.01)


