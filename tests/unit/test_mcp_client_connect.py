import os
from unittest.mock import AsyncMock, patch

import pytest

from openhands.core.config import OpenHandsConfig, load_from_env
from openhands.mcp.client import MCPClient
from openhands.mcp.utils import create_mcp_clients


@pytest.mark.asyncio
async def test_connect_http_with_dict_server(monkeypatch):
    """Test that connect_http properly handles dictionary server configs."""
    # Set environment variables for MCP HTTP server
    monkeypatch.setenv(
        'MCP_SHTTP_SERVERS',
        '[{"url": "http://env-server:8080", "api_key": "env-api-key"}]',
    )

    # Create a config object and load from environment
    config = OpenHandsConfig()
    load_from_env(config, os.environ)

    # Verify the environment variables were loaded into the config
    assert len(config.mcp.shttp_servers) == 1
    assert isinstance(config.mcp.shttp_servers[0], dict)

    # This is what we're testing - create_mcp_clients should handle dict server configs
    with patch.object(
        MCPClient, 'connect_http', new_callable=AsyncMock
    ) as mock_connect_http:
        await create_mcp_clients(
            sse_servers=[],
            stdio_servers=[],
            shttp_servers=config.mcp.shttp_servers,
            conversation_id=None,
        )

        # Check that connect_http was called
        mock_connect_http.assert_called_once()

        server_arg = mock_connect_http.call_args[0][0]

        # We're now passing the dictionary directly to connect_http
        # The conversion happens inside connect_http
        assert isinstance(server_arg, dict)
        assert server_arg.get('url') == 'http://env-server:8080'
        assert server_arg.get('api_key') == 'env-api-key'
