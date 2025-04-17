import asyncio
from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.mcp.tool import BaseTool, MCPClientTool


class MCPClient(BaseModel):
    """
    A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol.
    """

    session: Optional[ClientSession] = None
    exit_stack: AsyncExitStack = AsyncExitStack()
    description: str = 'MCP client tools for server interaction'
    tools: List[BaseTool] = Field(default_factory=list)
    tool_map: Dict[str, BaseTool] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    async def connect_sse(self, server_url: str, timeout: float = 30.0) -> None:
        """Connect to an MCP server using SSE transport.

        Args:
            server_url: The URL of the SSE server to connect to.
            timeout: Connection timeout in seconds. Default is 30 seconds.
        """
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        try:
            # Use asyncio.wait_for to enforce the timeout
            async def connect_with_timeout():
                streams_context = sse_client(
                    url=server_url,
                    timeout=timeout,  # Pass the timeout to sse_client
                )
                streams = await self.exit_stack.enter_async_context(streams_context)
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(*streams)
                )
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

    async def _initialize_and_list_tools(self) -> None:
        """Initialize session and populate tool map."""
        if not self.session:
            raise RuntimeError('Session not initialized.')

        await self.session.initialize()
        response = await self.session.list_tools()

        # Clear existing tools
        self.tools = []

        # Create proper tool objects for each server tool
        for tool in response.tools:
            server_tool = MCPClientTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.inputSchema,
                session=self.session,
            )
            self.tool_map[tool.name] = server_tool
            self.tools.append(server_tool)

        logger.info(
            f'Connected to server with tools: {[tool.name for tool in response.tools]}'
        )

    async def call_tool(self, tool_name: str, args: Dict):
        """Call a tool on the MCP server."""
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        return await self.tool_map[tool_name].execute(**args)

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        if self.session:
            try:
                # Close the session first
                if hasattr(self.session, 'close'):
                    await self.session.close()
                # Then close the exit stack
                await self.exit_stack.aclose()
            except Exception as e:
                logger.error(f'Error during disconnect: {str(e)}')
            finally:
                self.session = None
                self.tools = []
                logger.info('Disconnected from MCP server')
