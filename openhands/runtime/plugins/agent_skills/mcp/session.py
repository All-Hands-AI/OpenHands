from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client


@asynccontextmanager
async def _create_session(config: StdioServerParameters):
    """
    Create a temporary session for a single request.

    Args:
        config: Configuration dictionary for StdIO MCP servers

    Yields:
        An initialized ClientSession
    """
    # Set defaults for optional parameters
    args = config.get('args', [])
    env = config.get('env', None)
    encoding = config.get('encoding', 'utf-8')
    encoding_error_handler = config.get('encoding_error_handler', 'strict')

    # Create server parameters
    server_params = StdioServerParameters(
        command=config['command'],
        args=args,
        env=env,
        encoding=encoding,
        encoding_error_handler=encoding_error_handler,
    )

    # Create and yield session
    async with AsyncExitStack() as stack:
        try:
            stdio_transport = await stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            session = await stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            yield session
        except Exception as e:
            raise ConnectionError(f'Failed to connect to MCP server: {str(e)}') from e


async def list_tools(config: StdioServerParameters):
    """
    List all available tools from the MCP server.
    Automatically handles connection and cleanup.

    Args:
        config: Configuration dictionary for StdIO MCP servers

    Returns:
        List of tool objects

    Raises:
        ConnectionError: If connection to the server fails
        RuntimeError: If listing tools fails
    """
    async with _create_session(config) as session:
        try:
            response = await session.list_tools()
            return response.tools
        except Exception as e:
            raise RuntimeError(f'Failed to list tools: {str(e)}') from e


async def call_tool(
    config: StdioServerParameters,
    tool_name: str,
    input_data: dict[str, Any] | None = None,
):
    """
    Call a specific tool on the MCP server.
    Automatically handles connection and cleanup.

    Args:
        config: Configuration dictionary for StdIO MCP servers
        tool_name: Name of the tool to call
        input_data: Input data for the tool

    Returns:
        The tool's response

    Raises:
        ValueError: If tool name is empty
        ConnectionError: If connection to the server fails
        RuntimeError: If the tool call fails
    """
    if not tool_name:
        raise ValueError('Tool name cannot be empty')

    async with _create_session(config) as session:
        try:
            response = await session.call_tool(tool_name, input_data)
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to call tool '{tool_name}': {str(e)}") from e
