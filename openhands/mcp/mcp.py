from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import BaseModel, Field

from openhands.core.config.mcp_config import MCPConfig
from openhands.core.logger import openhands_logger as logger


class BaseTool(ABC, Tool):
    @classmethod
    def postfix(cls) -> str:
        return '_mcp_tool_call'

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool with given parameters."""

    def to_param(self) -> Dict:
        """Convert tool to function call format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name + self.postfix(),
                'description': self.description,
                'parameters': self.inputSchema,
            },
        }


class MCPClientTool(BaseTool):
    """Represents a tool proxy that can be called on the MCP server from the client side."""

    session: Optional[ClientSession] = None

    async def execute(self, **kwargs) -> CallToolResult:
        """Execute the tool by making a remote call to the MCP server."""
        if not self.session:
            return CallToolResult(
                content=[TextContent(text='Not connected to MCP server')], isError=True
            )

        try:
            result = await self.session.call_tool(self.name, kwargs)
            logger.debug(f'MCP tool result: {result}')
            return result
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f'Error executing tool: {str(e)}')],
                isError=True,
            )


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

    async def connect_sse(self, server_url: str) -> None:
        """Connect to an MCP server using SSE transport."""
        if not server_url:
            raise ValueError('Server URL is required.')
        if self.session:
            await self.disconnect()

        streams_context = sse_client(
            url=server_url, timeout=60, sse_read_timeout=60 * 10
        )
        streams = await self.exit_stack.enter_async_context(streams_context)
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(*streams)
        )

        await self._initialize_and_list_tools()

    async def connect_stdio(self, command: str, args: List[str]) -> None:
        """Connect to an MCP server using stdio transport."""
        if not command:
            raise ValueError('Server command is required.')
        if self.session:
            await self.disconnect()

        server_params = StdioServerParameters(command=command, args=args)
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


def convert_mcp_clients_to_tools(mcp_clients: list[MCPClient] | None) -> list[dict]:
    """
    Converts a list of MCPClient instances to ChatCompletionToolParam format
    that can be used by CodeActAgent.

    Args:
        mcp_clients: List of MCPClient instances or None

    Returns:
        List of dicts of tools ready to be used by CodeActAgent
    """
    if mcp_clients is None:
        logger.warning('mcp_clients is None, returning empty list')
        return []

    all_mcp_tools = []
    try:
        for client in mcp_clients:
            # Each MCPClient has an mcp_clients property that is a ToolCollection
            # The ToolCollection has a to_params method that converts tools to ChatCompletionToolParam format
            for tool in client.tools:
                mcp_tools = tool.to_param()
                all_mcp_tools.append(mcp_tools)
    except Exception as e:
        logger.error(f'Error in convert_mcp_clients_to_tools: {e}')
        return []
    return all_mcp_tools


async def create_mcp_clients(
    sse_mcp_server: List[str], commands: List[str], args: List[List[str]]
) -> List[MCPClient]:
    mcp_clients: List[MCPClient] = []
    # Initialize SSE connections
    if sse_mcp_server:
        for server_url in sse_mcp_server:
            logger.info(
                f'Initializing MCP agent for {server_url} with SSE connection...'
            )

            client = MCPClient()
            try:
                await client.connect_sse(server_url)
                mcp_clients.append(client)
                logger.info(f'Connected to MCP server {server_url} via SSE')
            except Exception as e:
                logger.error(f'Failed to connect to {server_url}: {str(e)}')
                raise

    # Initialize stdio connections
    if commands:
        for command, command_args in zip(commands, args):
            logger.info(
                f'Initializing MCP agent for {command} with stdio connection...'
            )

            client = MCPClient()
            try:
                await client.connect_stdio(command, command_args)
                mcp_clients.append(client)
                logger.info(f'Connected to MCP server via stdio with command {command}')
            except Exception as e:
                logger.error(f'Failed to connect with command {command}: {str(e)}')
                raise

    return mcp_clients

async def fetch_mcp_tools_from_config(mcp_config: MCPConfig) -> list[dict]:
    """
    Retrieves the list of MCP tools from the MCP clients.
    """
    mcp_clients = await create_mcp_clients(
        mcp_config.sse.mcp_servers, mcp_config.stdio.commands, mcp_config.stdio.args
    )
    mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
    for mcp_client in mcp_clients:
        await mcp_client.disconnect()
    return mcp_tools
