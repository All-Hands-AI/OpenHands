from typing import Optional
from openhands.core.config.loader import get_config

class MCPRouter:
    def __init__(self):
        self.config = get_config()
    
    def select_server(self, required_capabilities: list[str]) -> Optional[dict]:
        """Select the best MCP server based on required capabilities"""
        available_servers = [
            server for server in self.config.mcp_servers.values() 
            if server['enabled']
        ]
        
        for server in available_servers:
            if all(cap in server['capabilities'] for cap in required_capabilities):
                return server
        
        return available_servers[0] if available_servers else None

    def get_server_url(self, server_config: dict) -> str:
        """Generate server URL from config"""
        return f"http://{server_config['host']}:{server_config['port']}"