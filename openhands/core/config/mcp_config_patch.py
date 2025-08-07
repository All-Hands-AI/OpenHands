"""
Patch for the MCP config module to add the update_mcp_shttp_servers function.
This patch will be applied to the OpenHands MCP config module.
"""

from typing import List, Dict, Any

# Global variable to store the MCP SHTTP servers
_mcp_shttp_servers = []


def update_mcp_shttp_servers(servers: List[Dict[str, Any]]) -> None:
    """
    Update the MCP SHTTP servers configuration.
    
    Args:
        servers: List of MCP SHTTP server configurations
    """
    global _mcp_shttp_servers
    _mcp_shttp_servers = servers


def get_mcp_shttp_servers() -> List[Dict[str, Any]]:
    """
    Get the current MCP SHTTP servers configuration.
    
    Returns:
        List of MCP SHTTP server configurations
    """
    global _mcp_shttp_servers
    return _mcp_shttp_servers