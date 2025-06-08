from typing import Optional

from fastmcp import Client
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
from mcp import McpError
from mcp.types import CallToolResult
from pydantic import BaseModel, Field

from openhands.core.config.mcp_config import MCPSHTTPServerConfig, MCPSSEServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.tool import MCPClientTool


class MCPClient(BaseModel):
    """
    A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol.
    """

    client: Optional[Client] = None
    description: str = 'MCP client tools for server interaction'
    tools: list[MCPClientTool] = Field(default_factory=list)
    tool_map: dict[str, MCPClientTool] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    async def _initialize_and_list_tools(self) -> None:
        """Initialize session and populate tool map."""
        if not self.client:
            raise RuntimeError('Session not initialized.')

        async with self.client:
            tools = await self.client.list_tools()

        # Clear existing tools
        self.tools = []

        # Create proper tool objects for each server tool
        for tool in tools:
            server_tool = MCPClientTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.inputSchema,
                session=self.client,
            )
            self.tool_map[tool.name] = server_tool
            self.tools.append(server_tool)

        logger.info(f'Connected to server with tools: {[tool.name for tool in tools]}')

    async def connect_http(
        self,
        server: MCPSSEServerConfig | MCPSHTTPServerConfig,
        conversation_id: str | None = None,
        timeout: float = 30.0,
    ):
        """Connect to MCP server using SHTTP or SSE transport"""
        server_url = server.url
        api_key = server.api_key

        if not server_url:
            raise ValueError('Server URL is required.')

        try:
            headers = (
                {
                    'Authorization': f'Bearer {api_key}',
                    's': api_key,  # We need this for action execution server's MCP Router
                    'X-Session-API-Key': api_key,  # We need this for Remote Runtime
                }
                if api_key
                else {}
            )

            if conversation_id:
                headers['X-OpenHands-ServerConversation-ID'] = conversation_id

            # Instantiate custom transports due to custom headers
            if isinstance(server, MCPSHTTPServerConfig):
                transport = StreamableHttpTransport(
                    url=server_url,
                    headers=headers if headers else None,
                )
            else:
                transport = SSETransport(
                    url=server_url,
                    headers=headers if headers else None,
                )

            self.client = Client(transport, timeout=timeout)

            await self._initialize_and_list_tools()
        except McpError as e:
            logger.error(f'McpError connecting to {server_url}: {e}')
            raise  # Re-raise the error

        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {e}')
            raise

    async def call_tool(self, tool_name: str, args: dict) -> CallToolResult:
        """Call a tool on the MCP server."""
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        # The MCPClientTool is primarily for metadata; use the session to call the actual tool.
        if not self.client:
            raise RuntimeError('Client session is not available.')

        async with self.client:
            return await self.client.call_tool_mcp(name=tool_name, arguments=args)
