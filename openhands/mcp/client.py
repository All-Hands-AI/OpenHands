import asyncio
from typing import Optional

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.mcp.tool import MCPClientTool


class MCPClient(BaseModel):
    """
    A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol.
    """

    session: Optional[Client] = None
    description: str = 'MCP client tools for server interaction'
    tools: list[MCPClientTool] = Field(default_factory=list)
    tool_map: dict[str, MCPClientTool] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    async def _initialize_and_list_tools(self) -> None:
        """Initialize session and populate tool map."""
        if not self.session:
            raise RuntimeError('Session not initialized.')

        async with self.session:
            response = await self.session.list_tools()

        # Clear existing tools
        self.tools = []

        # Create proper tool objects for each server tool
        for tool in response:
            server_tool = MCPClientTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.inputSchema,
                session=self.session,
            )
            self.tool_map[tool.name] = server_tool
            self.tools.append(server_tool)

        logger.info(
            f'Connected to server with tools: {[tool.name for tool in response]}'
        )

    async def call_tool(self, tool_name: str, args: dict):
        """Call a tool on the MCP server."""
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        # The MCPClientTool is primarily for metadata; use the session to call the actual tool.
        if not self.session:
            raise RuntimeError('Client session is not available.')

        async with self.session:
            return await self.session.session.call_tool(name=tool_name, arguments=args)

    async def connect_http(
        self,
        server_url: str,
        api_key: str | None = None,
        conversation_id: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Connect to an MCP server using StreamableHTTP transport.

        Args:
            server_url: The URL of the StreamableHTTP server to connect to.
            api_key: Optional API key for authentication.
            conversation_id: Optional conversation ID for session tracking.
            timeout: Connection timeout in seconds. Default is 30 seconds.
        """
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        try:
            # Use asyncio.wait_for to enforce the timeout
            async def connect_with_timeout():
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

                transport = StreamableHttpTransport(url=server_url, headers=headers)

                self.session = Client(transport, timeout=timeout)
                await self._initialize_and_list_tools()

            # Apply timeout to the entire connection process
            await asyncio.wait_for(connect_with_timeout(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(
                f'Connection to {server_url} timed out after {timeout} seconds'
            )
            await self.disconnect()  # Clean up resources
            raise  # Re-raise the TimeoutError
        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {str(e)}')
            await self.disconnect()  # Clean up resources
            raise

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        if self.session:
            try:
                # Close the session first
                if hasattr(self.session, 'close'):
                    await self.session.close()
            except Exception as e:
                logger.error(f'Error during disconnect: {str(e)}')
            finally:
                self.session = None
                self.tools = []
                logger.info('Disconnected from MCP server')
