from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, TextContent, Tool
from pydantic import BaseModel, Field
from termcolor import colored

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
            connection_task = asyncio.create_task(self._connect_sse_internal(server_url))
            
            # Wait for the connection with timeout
            try:
                await asyncio.wait_for(connection_task, timeout=timeout)
            except TimeoutError:
                logger.error(f'Connection to {server_url} timed out after {timeout} seconds')
                # Cancel the connection task
                connection_task.cancel()
                try:
                    await connection_task
                except asyncio.CancelledError:
                    pass
                raise TimeoutError(f'Connection to {server_url} timed out after {timeout} seconds')
        except Exception as e:
            if not isinstance(e, TimeoutError):
                logger.error(f'Error connecting to {server_url}: {str(e)}')
            raise

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

    async def connect_stdio(self, command: str, args: List[str], envs: List[tuple[str, str]], timeout: float = 30.0) -> None:
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
            connection_task = asyncio.create_task(self._connect_stdio_internal(command, args, envs))
            
            # Wait for the connection with timeout
            try:
                await asyncio.wait_for(connection_task, timeout=timeout)
            except TimeoutError:
                logger.error(f'Connection to {command} timed out after {timeout} seconds')
                # Cancel the connection task
                connection_task.cancel()
                try:
                    await connection_task
                except asyncio.CancelledError:
                    pass
                raise TimeoutError(f'Connection to {command} timed out after {timeout} seconds')
        except Exception as e:
            if not isinstance(e, TimeoutError):
                logger.error(f'Error connecting to {command}: {str(e)}')
            raise

    async def _connect_stdio_internal(self, command: str, args: List[str], envs: List[tuple[str, str]]) -> None:
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
    sse_mcp_server: List[str], commands: List[str], args: List[List[str]], envs: List[List[tuple[str, str]]]
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
                # Don't raise the exception, just log it and continue
                # Make sure to disconnect the client to clean up resources
                try:
                    await client.disconnect()
                except Exception as disconnect_error:
                    logger.error(f'Error during disconnect after failed connection: {str(disconnect_error)}')

    # Initialize stdio connections
    if commands:
        for i, (command, command_args, command_envs) in enumerate(zip(commands, args, envs)):
            logger.info(
                f'Initializing MCP agent for {command} with stdio connection...'
            )

            client = MCPClient()
            try:
                await client.connect_stdio(command, command_args, command_envs)
                mcp_clients.append(client)
                logger.info(f'Connected to MCP server via stdio with command {command}')
            except Exception as e:
                logger.error(f'Failed to connect with command {command}: {str(e)}')
                # Don't raise the exception, just log it and continue
                # Make sure to disconnect the client to clean up resources
                try:
                    await client.disconnect()
                except Exception as disconnect_error:
                    logger.error(f'Error during disconnect after failed connection: {str(disconnect_error)}')

    return mcp_clients

async def fetch_mcp_tools_from_config(mcp_config: MCPConfig) -> list[dict]:
    """
    Retrieves the list of MCP tools from the MCP clients.
    
    Returns:
        A list of tool dictionaries. Returns an empty list if no connections could be established.
    """
    mcp_clients = []
    mcp_tools = []
    
    try:
        mcp_clients = await create_mcp_clients(
            mcp_config.sse.mcp_servers, mcp_config.stdio.commands, mcp_config.stdio.args, mcp_config.stdio.envs
        )
        
        if not mcp_clients:
            logger.warning("No MCP clients were successfully connected")
            return []
            
        mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
    except Exception as e:
        logger.error(f"Error fetching MCP tools: {str(e)}")
        return []
    finally:
        # Always disconnect clients to clean up resources
        for mcp_client in mcp_clients:
            try:
                await mcp_client.disconnect()
            except Exception as disconnect_error:
                logger.error(f"Error disconnecting MCP client: {str(disconnect_error)}")
    
    return mcp_tools
