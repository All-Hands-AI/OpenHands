"""
Initialize MCP configuration with default servers.
"""

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig


def create_default_mcp_config(host: str) -> MCPConfig:
    """
    Create a default MCP configuration with predefined servers.

    Args:
        host: Host string in the format "hostname:port".

    Returns:
        MCPConfig: A configuration with default MCP servers.
    """
    # Use the provided host
    mcp_host = host

    return MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url=f'http://{mcp_host}/mcp/sse', api_key=None)
        ],
        stdio_servers=[],
    )
