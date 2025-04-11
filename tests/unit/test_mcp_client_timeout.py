import asyncio
from contextlib import asynccontextmanager
from unittest import mock

import pytest

from openhands.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_connect_sse_timeout():
    """Test that connect_sse properly times out when server_url is invalid."""
    client = MCPClient()

    # Create a mock async context manager that simulates a timeout
    @asynccontextmanager
    async def mock_slow_context(*args, **kwargs):
        # This will hang for longer than our timeout
        await asyncio.sleep(10.0)
        yield (mock.AsyncMock(), mock.AsyncMock())

    # Patch the sse_client function to return our slow context manager
    with mock.patch(
        'openhands.mcp.client.sse_client', return_value=mock_slow_context()
    ):
        # Test with a very short timeout
        with pytest.raises(asyncio.TimeoutError):
            await client.connect_sse('http://example.com', timeout=0.1)
