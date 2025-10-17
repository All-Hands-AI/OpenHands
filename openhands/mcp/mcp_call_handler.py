import time

from openhands.core.config.mcp_config import MCPConfig
from openhands.events.action.mcp import MCPAction
from openhands.events.observation import (
    Observation,
)
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

    async def call_tool_mcp(
        self, action: MCPAction, mcp_config: MCPConfig
    ) -> Observation:
        mcp_client = await self.get_mcp_client(action, mcp_config)

        from openhands.mcp.utils import call_tool_mcp_direct

        # Call the tool and return the result
        # No need for try/finally since disconnect() is now just resetting state
        result = await call_tool_mcp_direct(mcp_client, action)
        return result

    async def get_mcp_client(self, action: MCPAction, config: MCPConfig) -> MCPClient:
        # Import here to avoid circular imports
        from openhands.mcp.utils import create_mcp_clients

        if not self.mcp_clients_map:
            # Create clients for this specific operation
            mcp_clients = await create_mcp_clients(
                config.sse_servers,
                config.shttp_servers,
                self.sid,
            )
            create_time = int(time.time())
            for mcp_client in mcp_clients:
                self.mcp_clients_map[mcp_client] = create_time
            self.mcp_config = config

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
        if not target_client:
            raise ValueError(
                f'No matching MCP agent found for tool name: {action.name}'
            )

        return target_client
