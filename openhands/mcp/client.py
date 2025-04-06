from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
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
            import asyncio
            from asyncio import TimeoutError

            # Create a task for the connection
            connection_task = asyncio.create_task(
                self._connect_sse_internal(server_url)
            )

            # Wait for the connection with timeout
            try:
                await asyncio.wait_for(connection_task, timeout=timeout)
            except TimeoutError:
                logger.error(
                    f'Connection to {server_url} timed out after {timeout} seconds'
                )
                # Cancel the connection task
                connection_task.cancel()
                try:
                    await connection_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {str(e)}')

    async def _connect_sse_internal(self, server_url: str) -> None:
        """Internal method to establish SSE connection."""
        streams_context = sse_client(
            url=server_url,
        )
        streams = await self.exit_stack.enter_async_context(streams_context)
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(*streams)
        )

        await self._initialize_and_list_tools()

    async def connect_stdio(
        self,
        command: str,
        args: List[str],
        envs: List[tuple[str, str]],
        timeout: float = 30.0,
    ) -> None:
        """Connect to an MCP server using stdio transport.

        Args:
            command: The command to execute.
            args: The arguments to pass to the command.
            envs: Environment variables as a list of tuples [name, value].
            timeout: Connection timeout in seconds. Default is 30 seconds.
        """
        if not command:
            raise ValueError('Server command is required.')
        if self.session:
            await self.disconnect()

        try:
            import asyncio
            from asyncio import TimeoutError

            # Create a task for the connection
            connection_task = asyncio.create_task(
                self._connect_stdio_internal(command, args, envs)
            )

            # Wait for the connection with timeout
            try:
                await asyncio.wait_for(connection_task, timeout=timeout)
            except TimeoutError:
                logger.error(
                    f'Connection to {command} timed out after {timeout} seconds'
                )
                # Cancel the connection task
                connection_task.cancel()
                try:
                    await connection_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.error(f'Error connecting to {command}: {str(e)}')

    async def _connect_stdio_internal(
        self, command: str, args: List[str], envs: List[tuple[str, str]]
    ) -> None:
        """Internal method to establish stdio connection."""
        envs_dict: dict[str, str] = {}
        for env in envs:
            envs_dict[env[0]] = env[1]
        server_params = StdioServerParameters(command=command, args=args, env=envs_dict)
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await self._initialize_and_list_tools()

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
