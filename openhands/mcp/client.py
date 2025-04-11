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
    tools: List[MCPClientTool] = Field(default_factory=list)
    tool_map: Dict[str, MCPClientTool] = Field(default_factory=dict)
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
            read_timeout: The read timeout for the SSE connection. Default is 2 minutes.
        """
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        # Store mnemonic separately for reconnection
        if mnemonic:
            self._original_mnemonic = mnemonic

        headers = {
            k: v for k, v in {'sid': sid, 'mnemonic': mnemonic}.items() if v is not None
        }
        without_mnemonic = {k: v for k, v in headers.items() if k != 'mnemonic'}
        self._server_params = {
            'url': server_url,
            'headers': headers if self.name is 'browser_mcp' else without_mnemonic,
            'timeout': timeout,
            'sse_read_timeout': read_timeout,
        }
        logger.info(f'sid: {sid}')
        logger.info('Connecting to MCP server')

        try:
            await self._connect_sse()
            await self._initialize_and_list_tools()
        except Exception as e:
            logger.error(f'Error connecting to {server_url}: {str(e)}')
            raise

    async def _connect_sse(
            self, 
        ) -> None:
        """Connect to an MCP server using SSE transport.

        Args:
            server_url: The URL of the SSE server to connect to.
            headers: The headers to send to the server.
            timeout: The timeout for the SSE connection.
            read_timeout: The read timeout for the SSE connection.
        """
        if not self._server_params['url']:
            raise ValueError('Server URL is required.')
        streams_context = sse_client(
                **self._server_params
            )
        streams = await self.exit_stack.enter_async_context(streams_context)
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(*streams)
        )
        tools = []
        if self.tool_map:
            for key in self.tool_map.keys():
                self.tool_map[key].session = self.session
                tools.append(self.tool_map[key])
        self.tools = tools

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

    async def call_tool(self, tool_name: str, args: Dict):
        """Call a tool on the MCP server with automatic reconnection on failure.

        Args:
            tool_name: Name of the tool to call.
            args: Arguments to pass to the tool.

        Returns:
            The tool execution result.

        Raises:
            ValueError: If the tool is not found.
            RuntimeError: If connection failed and couldn't be restored.
        """
        if tool_name not in self.tool_map:
            raise ValueError(f'Tool {tool_name} not found.')
        
        try:
            # Check if we need to reconnect
            await self._connect_sse()    
            await self.session.initialize()
            tool_result = await self.tool_map[tool_name].execute(**args)
            if tool_result.isError:
                logger.error(f'Tool call to {tool_name} failed: {tool_result.content}')
            return tool_result
        except Exception as e:
            logger.error(f'Tool call to {tool_name} failed: {str(e)}')
            # raise RuntimeError(
            #     f'Tool call to {tool_name} failed: {str(e)}'
            # )

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
