import asyncio
from unittest import mock

import pytest

from openhands.core.config.mcp_config import MCPConfig, MCPSSEConfig, MCPStdioConfig
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
    with mock.patch('openhands.mcp.mcp.MCPClient', return_value=mock_client):
        # Create a list of server URLs to test
        sse_servers = ['http://server1:8080', 'http://server2:8080']

        # Call create_mcp_clients with the server URLs
        clients = await create_mcp_clients(
            sse_mcp_server=sse_servers, commands=[], args=[], envs=[]
        )

        # Verify that no clients were successfully connected
        assert len(clients) == 0

        # Verify that connect_sse was called for each server
        assert mock_client.connect_sse.call_count == 2

        # Verify that disconnect was called for each failed connection
        assert mock_client.disconnect.call_count == 2


@pytest.mark.asyncio
async def test_stdio_connection_timeout():
    """Test that stdio connection timeout is handled gracefully."""
    # Create a mock MCPClient
    mock_client = mock.MagicMock(spec=MCPClient)

    # Configure the mock to raise a TimeoutError when connect_stdio is called
    async def mock_connect_stdio(*args, **kwargs):
        await asyncio.sleep(0.1)  # Simulate some delay
        raise asyncio.TimeoutError('Connection timed out')

    mock_client.connect_stdio.side_effect = mock_connect_stdio
    mock_client.disconnect = mock.AsyncMock()

    # Mock the MCPClient constructor to return our mock
    with mock.patch('openhands.mcp.mcp.MCPClient', return_value=mock_client):
        # Create test data for stdio connections
        commands = ['python', 'node']
        args = [['-m', 'server1'], ['server.js']]
        envs = [[['ENV1', 'VALUE1']], [['ENV2', 'VALUE2']]]

        # Call create_mcp_clients with the stdio configuration
        clients = await create_mcp_clients(
            sse_mcp_server=[], commands=commands, args=args, envs=envs
        )

        # Verify that no clients were successfully connected
        assert len(clients) == 0

        # Verify that connect_stdio was called for each command
        assert mock_client.connect_stdio.call_count == 2

        # Verify that disconnect was called for each failed connection
        assert mock_client.disconnect.call_count == 2


@pytest.mark.asyncio
async def test_fetch_mcp_tools_with_timeout():
    """Test that fetch_mcp_tools_from_config handles timeouts gracefully."""
    # Create a mock MCPConfig
    mock_config = mock.MagicMock(spec=MCPConfig)
    mock_config.sse = mock.MagicMock(spec=MCPSSEConfig)
    mock_config.stdio = mock.MagicMock(spec=MCPStdioConfig)

    # Configure the mock config
    mock_config.sse.mcp_servers = ['http://server1:8080']
    mock_config.stdio.commands = ['python']
    mock_config.stdio.args = [['-m', 'server1']]
    mock_config.stdio.envs = [[['ENV1', 'VALUE1']]]

    # Mock create_mcp_clients to return an empty list (simulating all connections failing)
    with mock.patch('openhands.mcp.mcp.create_mcp_clients', return_value=[]):
        # Call fetch_mcp_tools_from_config
        tools = await fetch_mcp_tools_from_config(mock_config)

        # Verify that an empty list of tools is returned
        assert tools == []


@pytest.mark.asyncio
async def test_mixed_connection_results():
    """Test that fetch_mcp_tools_from_config returns tools even when some connections fail."""
    # Create a mock MCPConfig
    mock_config = mock.MagicMock(spec=MCPConfig)
    mock_config.sse = mock.MagicMock(spec=MCPSSEConfig)
    mock_config.stdio = mock.MagicMock(spec=MCPStdioConfig)

    # Configure the mock config
    mock_config.sse.mcp_servers = ['http://server1:8080', 'http://server2:8080']
    mock_config.stdio.commands = []
    mock_config.stdio.args = []
    mock_config.stdio.envs = []

    # Create a successful client
    successful_client = mock.MagicMock(spec=MCPClient)
    successful_client.tools = [mock.MagicMock()]

    # Mock create_mcp_clients to return our successful client
    with mock.patch(
        'openhands.mcp.mcp.create_mcp_clients', return_value=[successful_client]
    ):
        # Call fetch_mcp_tools_from_config
        tools = await fetch_mcp_tools_from_config(mock_config)

        # Verify that tools were returned
        assert len(tools) > 0
