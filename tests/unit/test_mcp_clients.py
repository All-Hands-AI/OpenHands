import asyncio
from unittest import mock

import pytest

from openhands.mcp.mcp import MCPClients


@pytest.mark.asyncio
async def test_connect_sse_timeout():
    """Test that connect_sse handles timeout correctly."""
    # Create an instance of MCPClients
    mcp_clients = MCPClients()

    # Mock the sse_client function to simulate a timeout
    async def mock_sse_client(*args, **kwargs):
        # Simulate a delay longer than the timeout
        await asyncio.sleep(0.2)
        return mock.AsyncMock()

    # Mock the ClientSession to avoid actual connection attempts
    mock_session = mock.AsyncMock()

    # Mock the _initialize_and_list_tools method to avoid actual initialization
    async def mock_initialize_and_list_tools():
        pass

    # Apply the mocks
    with mock.patch(
        'openhands.mcp.mcp.sse_client', side_effect=mock_sse_client
    ), mock.patch(
        'openhands.mcp.mcp.ClientSession', return_value=mock_session
    ), mock.patch.object(
        MCPClients,
        '_initialize_and_list_tools',
        side_effect=mock_initialize_and_list_tools,
    ):
        # Set a very short timeout to ensure the test runs quickly
        timeout = 0.1

        # Call connect_sse with a short timeout
        await mcp_clients.connect_sse(server_url='http://example.com', timeout=timeout)

        # Verify that the session is still None (connection failed)
        assert mcp_clients.session is None


@pytest.mark.asyncio
async def test_connect_sse_success():
    """Test that connect_sse succeeds when connection is established within timeout."""
    # Create an instance of MCPClients
    mcp_clients = MCPClients()

    # Create a mock context manager for sse_client
    class MockSSEClientContextManager:
        async def __aenter__(self):
            return (mock.AsyncMock(), mock.AsyncMock())

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Mock the sse_client function to return our context manager
    def mock_sse_client(*args, **kwargs):
        return MockSSEClientContextManager()

    # Mock the ClientSession to avoid actual connection attempts
    mock_session = mock.AsyncMock()

    # Mock the _initialize_and_list_tools method to avoid actual initialization
    async def mock_initialize_and_list_tools():
        pass

    # Apply the mocks
    with mock.patch(
        'openhands.mcp.mcp.sse_client', side_effect=mock_sse_client
    ), mock.patch(
        'openhands.mcp.mcp.ClientSession', return_value=mock_session
    ), mock.patch.object(
        MCPClients,
        '_initialize_and_list_tools',
        side_effect=mock_initialize_and_list_tools,
    ):
        # Set a reasonable timeout
        timeout = 1.0

        # Call connect_sse
        await mcp_clients.connect_sse(server_url='http://example.com', timeout=timeout)

        # Verify that the session is set (connection succeeded)
        assert mcp_clients.session is not None


@pytest.mark.asyncio
async def test_connect_stdio_timeout():
    """Test that connect_stdio handles timeout correctly."""
    # Create an instance of MCPClients
    mcp_clients = MCPClients()

    # Mock the stdio_client function to simulate a timeout
    async def mock_stdio_client(*args, **kwargs):
        # Simulate a delay longer than the timeout
        await asyncio.sleep(0.2)
        return mock.AsyncMock()

    # Mock the ClientSession to avoid actual connection attempts
    mock_session = mock.AsyncMock()

    # Mock the _initialize_and_list_tools method to avoid actual initialization
    async def mock_initialize_and_list_tools():
        pass

    # Apply the mocks
    with mock.patch(
        'openhands.mcp.mcp.stdio_client', side_effect=mock_stdio_client
    ), mock.patch(
        'openhands.mcp.mcp.ClientSession', return_value=mock_session
    ), mock.patch.object(
        MCPClients,
        '_initialize_and_list_tools',
        side_effect=mock_initialize_and_list_tools,
    ):
        # Set a very short timeout to ensure the test runs quickly
        timeout = 0.1

        # Call connect_stdio with a short timeout
        await mcp_clients.connect_stdio(
            command='python', args=['-m', 'server'], timeout=timeout
        )

        # Verify that the session is still None (connection failed)
        assert mcp_clients.session is None


@pytest.mark.asyncio
async def test_connect_stdio_success():
    """Test that connect_stdio succeeds when connection is established within timeout."""
    # Create an instance of MCPClients
    mcp_clients = MCPClients()

    # Create a mock context manager for stdio_client
    class MockStdioClientContextManager:
        async def __aenter__(self):
            return (mock.AsyncMock(), mock.AsyncMock())

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Mock the stdio_client function to return our context manager
    def mock_stdio_client(*args, **kwargs):
        return MockStdioClientContextManager()

    # Mock the ClientSession to avoid actual connection attempts
    mock_session = mock.AsyncMock()

    # Mock the _initialize_and_list_tools method to avoid actual initialization
    async def mock_initialize_and_list_tools():
        pass

    # Apply the mocks
    with mock.patch(
        'openhands.mcp.mcp.stdio_client', side_effect=mock_stdio_client
    ), mock.patch(
        'openhands.mcp.mcp.ClientSession', return_value=mock_session
    ), mock.patch.object(
        MCPClients,
        '_initialize_and_list_tools',
        side_effect=mock_initialize_and_list_tools,
    ):
        # Set a reasonable timeout
        timeout = 1.0

        # Call connect_stdio
        await mcp_clients.connect_stdio(
            command='python', args=['-m', 'server'], timeout=timeout
        )

        # Verify that the session is set (connection succeeded)
        assert mcp_clients.session is not None
