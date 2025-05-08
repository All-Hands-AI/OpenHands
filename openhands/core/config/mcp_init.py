"""
Initialize MCP configuration with default servers.
"""

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig

def create_default_mcp_config() -> MCPConfig:
    """
    Create a default MCP configuration with predefined servers.
    
    Returns:
        MCPConfig: A configuration with default MCP servers.
    """
    return MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url="http://localhost:12000/mcp", api_key=None),
            MCPSSEServerConfig(url="http://localhost:3000/mcp", api_key=None)
        ],
        stdio_servers=[]
    )