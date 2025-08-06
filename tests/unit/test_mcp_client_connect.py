import pytest

from openhands.core.config.mcp_config import MCPSHTTPServerConfig
from openhands.mcp.utils import create_mcp_clients


def test_convert_dict_to_mcp_http_server_config():
    """Test direct conversion of dictionary to MCPSHTTPServerConfig."""
    # Create a dictionary server configuration
    dict_server = {'url': 'http://env-server:8080', 'api_key': 'env-api-key'}
    
    # Convert the dictionary to an MCPSHTTPServerConfig object
    server_config = MCPSHTTPServerConfig(**dict_server)
    
    # Verify the conversion
    assert isinstance(server_config, MCPSHTTPServerConfig)
    assert server_config.url == 'http://env-server:8080'
    assert server_config.api_key == 'env-api-key'


@pytest.mark.asyncio
async def test_create_mcp_clients_with_server_config(monkeypatch):
    """Test that create_mcp_clients works with proper server config objects."""
    # Create a proper server configuration object
    server_config = MCPSHTTPServerConfig(url='http://env-server:8080', api_key='env-api-key')
    
    # Patch the connect_http method to avoid actual HTTP requests
    monkeypatch.setattr(
        'openhands.mcp.client.MCPClient.connect_http',
        lambda self, server, conversation_id=None, timeout=30.0: None
    )
    
    # Call create_mcp_clients with the proper server config object
    await create_mcp_clients(
        sse_servers=[],
        stdio_servers=[],
        shttp_servers=[server_config],
        conversation_id=None,
    )
