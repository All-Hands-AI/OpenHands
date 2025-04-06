from openhands.core.config.mcp_config import MCPConfig, MCPStdioConfigEntry
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.client import MCPClient


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
    sse_mcp_server: list[str],
    stdio_mcp_tool_configs: dict[str, MCPStdioConfigEntry],
) -> list[MCPClient]:
    mcp_clients: list[MCPClient] = []
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
                    logger.error(
                        f'Error during disconnect after failed connection: {str(disconnect_error)}'
                    )

    # Initialize stdio connections
    if stdio_mcp_tool_configs:
        for name, tool in stdio_mcp_tool_configs.items():
            logger.info(
                f'Initializing MCP tool [{name}] for [{tool.command}] with stdio connection...'
            )
            client = MCPClient()
            try:
                await client.connect_stdio(
                    tool.command,
                    tool.args,
                    [(k, v) for k, v in tool.env.items()],
                )
                mcp_clients.append(client)
                logger.info(
                    f'Connected to MCP server via stdio with command {tool.command}'
                )
            except Exception as e:
                logger.error(f'Failed to connect with command {tool.command}: {str(e)}')
                # Don't raise the exception, just log it and continue
                # Make sure to disconnect the client to clean up resources
                try:
                    await client.disconnect()
                except Exception as disconnect_error:
                    logger.error(
                        f'Error during disconnect after failed connection: {str(disconnect_error)}'
                    )
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
        logger.debug(f'Creating MCP clients with config: {mcp_config}')
        mcp_clients = await create_mcp_clients(
            mcp_config.sse.mcp_servers,
            mcp_config.stdio.tools,
        )

        if not mcp_clients:
            logger.warning('No MCP clients were successfully connected')
            return []

        mcp_tools = convert_mcp_clients_to_tools(mcp_clients)
    except Exception as e:
        logger.error(f'Error fetching MCP tools: {str(e)}')
        return []
    finally:
        # Always disconnect clients to clean up resources
        for mcp_client in mcp_clients:
            try:
                await mcp_client.disconnect()
            except Exception as disconnect_error:
                logger.error(f'Error disconnecting MCP client: {str(disconnect_error)}')

    logger.debug(f'MCP tools: {mcp_tools}')
    return mcp_tools
