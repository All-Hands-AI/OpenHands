from typing import Optional

from fastmcp.client import Client
from pydantic import BaseModel, Field

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
        server_url: str,
        api_key: str | None = None,
        conversation_id: str | None = None,
        timeout: float = 30.0,
    ):
        """Connect to MCP server using SHTTP or SSE transport"""
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.client:
            await self.disconnect()

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
                headers['X-OpenHands-Conversation-ID'] = conversation_id

            self.client = Client(
                server_url, headers=headers if headers else None, timeout=timeout
            )

            await self._initialize_and_list_tools()
        except TimeoutError:
            logger.error(
                f'Connection to {server_url} timed out after {timeout} seconds'
            )
            await self.disconnect()  # Clean up resources
            raise  # Re-raise the TimeoutError

        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {str(e)}')
            await self.disconnect()  # Clean up resources
            raise

    async def call_tool(self, tool_name: str, args: dict):
        """Call a tool on the MCP server."""
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        # The MCPClientTool is primarily for metadata; use the session to call the actual tool.
        if not self.client:
            raise RuntimeError('Client session is not available.')

        async with self.client:
            await self.client.call_tool_mcp(name=tool_name, arguments=args)

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f'Error during disconnect: {str(e)}')
            finally:
                self.client = None
                self.tools = []
                logger.info('Disconnected from MCP server')
