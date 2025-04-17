import asyncio
from unittest import mock

import pytest

from openhands.core.config.mcp_config import MCPConfig
from openhands.mcp import MCPClient, create_mcp_clients, fetch_mcp_tools_from_config


@pytest.mark.asyncio
async def test_sse_connection_timeout():
    """Test that SSE connection timeout is handled gracefully."""
    # Create a mock MCPClient
    mock_client = mock.MagicMock(spec=MCPClient)

    # Configure the mock to raise a TimeoutError when connect_sse is called
    async def mock_connect_sse(*args, **kwargs):
        await asyncio.sleep(0.1)  # Simulate some delay
        raise asyncio.TimeoutError('Connection timed out')

    mock_client.connect_sse.side_effect = mock_connect_sse
    mock_client.disconnect = mock.AsyncMock()

    # Mock the MCPClient constructor to return our mock
    with mock.patch('openhands.mcp.utils.MCPClient', return_value=mock_client):
        # Create a list of server URLs to test
        servers = ['http://server1:8080', 'http://server2:8080']

        # Call create_mcp_clients with the server URLs
        clients = await create_mcp_clients(mcp_servers=servers)

        # Verify that no clients were successfully connected
        assert len(clients) == 0

        # Verify that connect_sse was called for each server
        assert mock_client.connect_sse.call_count == 2

        # Verify that disconnect was called for each failed connection
        assert mock_client.disconnect.call_count == 2


@pytest.mark.asyncio
async def test_fetch_mcp_tools_with_timeout():
    """Test that fetch_mcp_tools_from_config handles timeouts gracefully."""
    # Create a mock MCPConfig
    mock_config = mock.MagicMock(spec=MCPConfig)

    # Configure the mock config
    mock_config.mcp_servers = ['http://server1:8080']

    # Mock create_mcp_clients to return an empty list (simulating all connections failing)
    with mock.patch('openhands.mcp.utils.create_mcp_clients', return_value=[]):
        # Call fetch_mcp_tools_from_config
        tools = await fetch_mcp_tools_from_config(mock_config)

        # Verify that an empty list of tools is returned
        assert tools == []


@pytest.mark.asyncio
async def test_mixed_connection_results():
    """Test that fetch_mcp_tools_from_config returns tools even when some connections fail."""
    # Create a mock MCPConfig
    mock_config = mock.MagicMock(spec=MCPConfig)

    # Configure the mock config
    mock_config.mcp_servers = ['http://server1:8080', 'http://server2:8080']

    # Create a successful client
    successful_client = mock.MagicMock(spec=MCPClient)
    successful_client.tools = [mock.MagicMock()]

    # Mock create_mcp_clients to return our successful client
    with mock.patch(
        'openhands.mcp.utils.create_mcp_clients', return_value=[successful_client]
    ):
        # Call fetch_mcp_tools_from_config
        tools = await fetch_mcp_tools_from_config(mock_config)

        # Verify that tools were returned
        assert len(tools) > 0
