from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.routing import Mount

from openhands.core.config.mcp_config import MCPStdioServerConfig
from openhands.runtime.mcp.proxy.manager import MCPProxyManager


@pytest.fixture
def mock_proxy():
    """Create a mock FastMCP proxy"""
    mock_proxy = Mock()
    mock_proxy.http_app.return_value = Mock()
    return mock_proxy


@pytest.fixture
def manager(mock_proxy):
    """Create an instance of MCPProxyManager"""
    manager = MCPProxyManager(auth_enabled=False)
    manager.proxy = mock_proxy
    manager.config = {
        'mcpServers': {
            'test_server': {'command': 'python', 'args': ['-m', 'test_server']}
        }
    }
    return manager


@pytest.mark.asyncio
async def test_mount_to_app_removes_existing_mounts(manager: MCPProxyManager):
    """Test that existing /mcp and / mounts are removed during mounting"""

    app = FastAPI()
    app.mount('/mcp', Mock())
    app.mount('/', Mock())
    app.mount('/api', Mock())

    stdio_servers = [
        MCPStdioServerConfig(name='server1', command='python', args=['-m', 'server1']),
        MCPStdioServerConfig(name='server2', command='python', args=['-m', 'server2']),
    ]

    # Execute mounting
    await manager.update_and_remount(app, stdio_servers)

    # Verify new mounts have been added
    now_mcp_mounts = [
        route
        for route in app.routes
        if isinstance(route, Mount) and route.path == '/mcp'
    ]
    now_root_mounts = [
        route for route in app.routes if isinstance(route, Mount) and route.path == '/'
    ]

    assert len(now_mcp_mounts) == 1, 'There should be one /mcp mount'
    assert len(now_root_mounts) == 1, 'There should be one / mount'
