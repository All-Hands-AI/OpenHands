"""
Initialize MCP configuration with default servers.
"""

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig, MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger

def create_default_mcp_config() -> MCPConfig:
    """
    Create a default MCP configuration with predefined servers.
    
    Returns:
        MCPConfig: A configuration with default MCP servers.
    """
    # Define the default MCP servers
    
    return MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url="http://localhost:3000/mcp/sse", api_key=None)
        ],
        stdio_servers=[
            
        ]
    )