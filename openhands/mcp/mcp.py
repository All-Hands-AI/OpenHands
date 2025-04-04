from contextlib import AsyncExitStack
from typing import Dict, List, Optional
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import ImageContent, TextContent

from openhands.core.logger import openhands_logger as logger
from openhands.mcp.mcp_base import BaseTool, ExtendedImageContent, ToolResult
from openhands.mcp.mcp_tool_collection import ToolCollection


class MCPClientTool(BaseTool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool by making a remote call to the MCP server."""
        if not self.session:
            return ToolResult(error='Not connected to MCP server')

        try:
            result = await self.session.call_tool(self.name, kwargs)
            logger.debug(f'MCP tool result: {result}')
            content_str = ', '.join(
                item.text for item in result.content if isinstance(item, TextContent)
            )

            # special case for image content
            if (
                self.name == 'browser_screenshot'
                and isinstance(result.content, list)
                and len(result.content) > 0
                and isinstance(result.content[0], ImageContent)
            ):
                screenshot_content = result.content[0]
                if screenshot_content.url is not None:
                    logger.debug(
                        f'MCP screenshot content url: {screenshot_content.url}'
                    )
                    return ToolResult(
                        output=ExtendedImageContent(
                            url=screenshot_content.url,
                            mimeType=screenshot_content.mimeType,
                            data=screenshot_content.data,
                            type=screenshot_content.type,
                            annotations=screenshot_content.annotations,
                        )
                    )
                else:
                    return ToolResult(output=result.content[0])
            return ToolResult(output=content_str or 'No output returned.')
        except Exception as e:
            return ToolResult(error=f'Error executing tool: {str(e)}')


class MCPClients(ToolCollection):
    """
    A collection of tools that connects to an MCP server and manages available tools through the Model Context Protocol.
    """

    session: Optional[ClientSession] = None
    exit_stack: AsyncExitStack = AsyncExitStack()
    description: str = 'MCP client tools for server interaction'

    def __init__(self):
        super().__init__()  # Initialize with empty tools list
        self.name = 'mcp'  # Keep name for backward compatibility

    async def connect_sse(
        self,
        server_url: str,
        sid: Optional[str] = None,
        user_id: Optional[str] = None,
        mnemonic: Optional[str] = None,
        timeout: float = 5,
    ) -> None:
        """Connect to an MCP server using SSE transport.
        
        Args:
            server_url: The URL of the MCP server
            sid: Optional session ID
            user_id: Optional user ID
            mnemonic: Optional mnemonic
            timeout: Connection timeout in seconds (default: 5.0)
        """
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        # # Query user from database if user_id is provided
        # if not user_id:
        #     raise ValueError('User ID is required.')

        headers = {
            k: v for k, v in {'sid': sid, 'mnemonic': None}.items() if v is not None
        }
        logger.info(f'sid: {sid}')
        logger.info('Connecting to MCP server')
        
        try:
            streams_context = sse_client(
                url=server_url, timeout=timeout, sse_read_timeout=15, headers=headers
            )
            logger.info('Connected to MCP server')
            
            async def connect_with_timeout():
                streams = await self.exit_stack.enter_async_context(streams_context)
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(*streams)
                )
                logger.info('Connected to MCP server with client session')
                await self._initialize_and_list_tools()
                
            await asyncio.wait_for(connect_with_timeout(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f'Connection to MCP server timed out after {timeout} seconds')
        except Exception as e:
            logger.error(f'Error connecting to MCP server: {str(e)}')

    async def connect_stdio(self, command: str, args: List[str], timeout: float = 5.0) -> None:
        """Connect to an MCP server using stdio transport.
        
        Args:
            command: The command to execute
            args: List of arguments for the command
            timeout: Connection timeout in seconds (default: 5.0)
        """
        if not command:
            raise ValueError('Server command is required.')
        if self.session:
            await self.disconnect()

        try:
            server_params = StdioServerParameters(command=command, args=args)
            
            async def connect_with_timeout():
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )
                await self._initialize_and_list_tools()
                
            await asyncio.wait_for(connect_with_timeout(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f'Connection to MCP server via stdio timed out after {timeout} seconds')
        except Exception as e:
            logger.error(f'Error connecting to MCP server via stdio: {str(e)}')

    async def _initialize_and_list_tools(self) -> None:
        """Initialize session and populate tool map."""
        if not self.session:
            raise RuntimeError('Session not initialized.')

        await self.session.initialize()
        response = await self.session.list_tools()

        # Clear existing tools
        self.tools = tuple()
        self.tool_map: Dict[str, BaseTool] = {}

        # Create proper tool objects for each server tool
        for tool in response.tools:
            server_tool = MCPClientTool(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
                session=self.session,
            )
            self.tool_map[tool.name] = server_tool

        self.tools = tuple(self.tool_map.values())
        logger.info(
            f'Connected to server with tools: {[tool.name for tool in response.tools]}'
        )

    async def disconnect(self) -> None:
        """Disconnect from the MCP server and clean up resources."""
        if self.session:
            await self.exit_stack.aclose()
            self.session = None
            self.tools = tuple()
            self.tool_map = {}
            logger.info('Disconnected from MCP server')
