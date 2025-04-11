import asyncio
from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client
from pydantic import BaseModel, Field

from openhands.core.logger import openhands_logger as logger
from openhands.mcp.tool import BaseTool, MCPClientTool


class MCPClient(BaseModel):
    """A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol."""

    session: Optional[ClientSession] = None
    exit_stack: AsyncExitStack = AsyncExitStack()
    description: str = 'MCP client tools for server interaction'
    tools: List[BaseTool] = Field(default_factory=list)
    tool_map: Dict[str, BaseTool] = Field(default_factory=dict)
    name: str = Field(default='')

    class Config:
        arbitrary_types_allowed = True

    async def connect_sse(
        self,
        server_url: str,
        sid: Optional[str] = None,
        mnemonic: Optional[str] = None,
        timeout: float = 5.0,
        read_timeout: float = 60.0 * 2, # 2 minutes instead of default 5 minutes
    ) -> None:
        """Connect to an MCP server using SSE transport.

        Args:
            server_url: The URL of the SSE server to connect to.
            timeout: Connection timeout in seconds. Default is 5 seconds.
            sid: The session id.
            mnemonic: The mnemonic for the session.
        """
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        # Store connection parameters for reconnection
        self._connection_params = {
            'server_url': server_url,
            'sid': sid,
            'timeout': timeout,
        }

        # Store mnemonic separately for reconnection
        if mnemonic:
            self._original_mnemonic = mnemonic

        headers = {
            k: v for k, v in {'sid': sid, 'mnemonic': mnemonic}.items() if v is not None
        }
        logger.info(f'sid: {sid}')
        logger.info('Connecting to MCP server')

        try:
            streams_context = sse_client(
                url=server_url,
                headers=headers,
                timeout=timeout,
                read_timeout=read_timeout,
            )
            streams = await self.exit_stack.enter_async_context(streams_context)
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(*streams)
            )

            await self._initialize_and_list_tools()
        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {str(e)}')
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

    async def is_connected(self) -> bool:
        """Check if the client is connected to the MCP server.

        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.session:
            return False

        try:
            # Try a lightweight operation to check connection
            await self.session.send_ping()
            return True
        except Exception:
            return False

    async def reconnect(self, max_retries: int = 3) -> bool:
        """Attempt to reconnect to the MCP server.

        Args:
            max_retries: Maximum number of reconnection attempts.

        Returns:
            bool: True if reconnection was successful, False otherwise.
        """
        if not hasattr(self, '_connection_params'):
            logger.error('No previous connection parameters found.')
            return False

        # First ensure we're fully disconnected to clean up any lingering connections
        for attempt in range(max_retries):
            try:
                await self.disconnect()
                logger.info(f'Reconnection attempt {attempt + 1}/{max_retries}')
                # Get params from stored connection parameters
                params = self._connection_params.copy()
                await self.connect_sse(**params)  # type: ignore
                return True
            except Exception as e:
                logger.error(f'Reconnection attempt {attempt + 1} failed: {str(e)}')
            # Wait before trying again
            backoff_time = min(2**attempt, 30)
            logger.info(f'Waiting {backoff_time}s before next reconnection attempt')
            await asyncio.sleep(backoff_time)  # Exponential backoff with max 30s

        logger.error('All reconnection attempts failed')
        return False

    async def call_tool(self, tool_name: str, args: Dict, max_retries: int = 3):
        """Call a tool on the MCP server with automatic reconnection on failure.

        Args:
            tool_name: Name of the tool to call.
            args: Arguments to pass to the tool.
            max_retries: Maximum number of retry attempts.

        Returns:
            The tool execution result.

        Raises:
            ValueError: If the tool is not found.
            RuntimeError: If connection failed and couldn't be restored.
        """
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        tool_result = None
        for attempt in range(max_retries + 1):
            try:
                tool_result = await self.tool_map[tool_name].execute(**args)
                if tool_result.isError:
                    await self.reconnect(max_retries=2)
                    continue
                return tool_result
            except Exception as e:
                logger.error(f'Tool call to {tool_name} failed: {str(e)}')
                raise RuntimeError(
                    f'Tool call to {tool_name} in {attempt} retries: {str(e)}'
                )
        return tool_result

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
