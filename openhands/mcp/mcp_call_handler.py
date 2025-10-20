import time

from openhands.core.config.mcp_config import (
    MCPSHTTPServerConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.events.action.mcp import MCPAction
from openhands.mcp.client import MCPClient


class MCPCallHandler:
    """Supports retrieving the target mcp_client by tool_name to initiate calls,
    through building an mcp_client cache and enabling a default 60-second delayed update."""

    def __init__(
        self,
        sid: str = 'default',
    ):
        self.sid = sid
        self.mcp_clients_map: dict[MCPClient, int] = {}

    async def get_mcp_client(
        self,
        action: MCPAction,
        sse_servers: list[MCPSSEServerConfig],
        shttp_servers: list[MCPSHTTPServerConfig],
        stdio_servers: list[MCPStdioServerConfig] | None = None,
    ) -> MCPClient:
        # Import here to avoid circular imports
        from openhands.mcp.utils import create_mcp_clients

        if not self.mcp_clients_map:
            # Create clients for this specific operation
            mcp_clients: list[MCPClient]
            mcp_clients = await create_mcp_clients(
                sse_servers,
                shttp_servers,
                self.sid,
                stdio_servers,
            )
            create_time = int(time.time())
            for mcp_client in mcp_clients:
                self.mcp_clients_map[mcp_client] = create_time

        tool_name = action.name
        # Searches for a client that has the requested tool registered
        # in its tool map
        target_client = next(
            (c for c in self.mcp_clients_map if tool_name in c.tool_map), None
        )

        # Updates clients whose cached state exceeds the 60-second
        # validity threshold
        if not target_client:
            now_time = int(time.time())
            for mcp_client, refresh_time in self.mcp_clients_map.items():
                if now_time - refresh_time > 60:
                    await mcp_client.refresh()
                if tool_name in mcp_client.tool_map:
                    target_client = mcp_client

        return target_client
