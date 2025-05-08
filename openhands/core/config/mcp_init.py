"""
Initialize MCP configuration with default servers.
"""

from openhands.core.config.mcp_config import MCPConfig, MCPSSEServerConfig
from openhands.core.logger import openhands_logger as logger

def create_default_mcp_config() -> MCPConfig:
    """
    Create a default MCP configuration with predefined servers.
    
    Returns:
        MCPConfig: A configuration with default MCP servers.
    """
    # Define the default MCP servers
    # The runtime will add itself as an additional server
    # Connection failures to these servers will be handled gracefully
    logger.info("Initializing default MCP configuration with localhost:3000/mcp")
    
    return MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url="http://localhost:3000/mcp", api_key=None)
        ],
        stdio_servers=[]
    )