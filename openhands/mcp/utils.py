import asyncio
import json
import re
from typing import Any, Optional

from mcp.types import CallToolResult, ImageContent, TextContent

from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.search_engine import SearchEngineConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.observation import ObservationType
from openhands.events.action.mcp import McpAction
from openhands.events.observation.commands import IPythonRunCellObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.mcp import MCPObservation
from openhands.events.observation.observation import Observation
from openhands.events.observation.planner_mcp import PlanObservation
from openhands.events.observation.playwright_mcp import (
    BrowserMCPObservation,
)
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


async def connect_single_client(
    name: str,
    mcp_config: MCPConfig,
    sid: Optional[str] = None,
    mnemonic: Optional[str] = None,
) -> Optional[MCPClient]:
    """Connect to a single MCP server and return the client or None on failure."""
    logger.info(
        f'Initializing MCP {name} agent for {mcp_config.url} with {mcp_config.mode} connection...'
    )

    client = MCPClient(name=name)
    try:
        await client.connect_sse(mcp_config.url, sid, mnemonic)
        logger.info(f'Connected to MCP server {mcp_config.url} via SSE')
        return client
    except Exception as e:
        logger.error(f'Failed to connect to {mcp_config.url}: {str(e)}')
        try:
            await client.disconnect()
        except Exception as disconnect_error:
            logger.error(
                f'Error during disconnect after failed connection: {str(disconnect_error)}'
            )
        return None


async def create_mcp_clients(
    dict_mcp_config: dict[str, MCPConfig],
    sid: Optional[str] = None,
    mnemonic: Optional[str] = None,
) -> list[MCPClient]:
    """Create MCP clients with concurrent connections for better performance."""

    # Create connection tasks for all MCP configs concurrently
    connection_tasks = []
    for name, config in dict_mcp_config.items():
        # Skip if this is a search engine config
        # if f'search_engine' not in name:
        connection_tasks.append(connect_single_client(name, config, sid, mnemonic))

    # Execute all connections concurrently
    results = await asyncio.gather(*connection_tasks, return_exceptions=True)

    # Collect successful clients, filtering out None values and exceptions
    mcp_clients: list[MCPClient] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f'Unexpected error during MCP client connection: {result}')
        elif result is not None and isinstance(result, MCPClient):
            mcp_clients.append(result)

    return mcp_clients


async def fetch_mcp_tools_from_config(
    dict_mcp_config: dict[str, MCPConfig],
    sid: Optional[str] = None,
    mnemonic: Optional[str] = None,
) -> list[dict]:
    """
    Retrieves the list of MCP tools from the MCP clients.

    Returns:
        A list of tool dictionaries. Returns an empty list if no connections could be established.
    """
    mcp_clients = []
    mcp_tools = []
    try:
        logger.debug(f'Creating MCP clients with config: {dict_mcp_config}')
        mcp_clients = await create_mcp_clients(
            dict_mcp_config,
            sid=sid,
            mnemonic=mnemonic,
        )

        if not mcp_clients:
            logger.warning('No MCP clients were successfully connected')
            return []

        mcp_tools = convert_mcp_clients_to_tools(mcp_clients)

        # Always disconnect clients to clean up resources
        disconnect_tasks = [mcp_client.disconnect() for mcp_client in mcp_clients]
        results = await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Log any errors that occurred during disconnection
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Error disconnecting MCP client: {str(result)}')
    except Exception as e:
        logger.error(f'Error fetching MCP tools: {str(e)}')
        return []

    # logger.debug(f'MCP tools: {mcp_tools}')
    return mcp_tools


async def fetch_search_tools_from_config(
    dict_search_engine_config: dict[str, SearchEngineConfig],
    sid: Optional[str] = None,
    mnemonic: Optional[str] = None,
) -> list[dict]:
    """
    Retrieves the list of search tools from the search engine config.
    """
    search_tools = []
    try:
        for name, search_engine_config in dict_search_engine_config.items():
            if search_engine_config.type.startswith('mcp'):
                mcp_mode = search_engine_config.type.split('_')[1]
                dict_mcp_config = {}
                dict_mcp_config[f'search_engine_{name}'] = MCPConfig(
                    url=search_engine_config.url,
                    mode=mcp_mode,
                )

                tools = await fetch_mcp_tools_from_config(
                    dict_mcp_config,
                    sid=sid,
                    mnemonic=mnemonic,
                )
                if search_engine_config.tools:
                    tools = [
                        tool
                        for tool in tools
                        if tool['name'] in search_engine_config.tools
                    ]
                search_tools += tools
        return search_tools
    except Exception as e:
        logger.error(f'Error fetching search tools: {str(e)}')
        return []


async def call_tool_mcp(mcp_clients: list[MCPClient], action: McpAction) -> Observation:
    """Call a tool on an MCP server and return the observation.

    Args:
        mcp_clients: List of MCPClient instances
        action: The MCP action to execute

    Returns:
        The observation from the MCP server
    """
    if not mcp_clients:
        raise ValueError('No MCP clients found')
    logger.info(f'MCP action received: {action}')
    # Find the MCP agent that has the matching tool name
    matching_client = None
    logger.info(f'MCP action name: {action.name}')
    for client in mcp_clients:
        if action.name in [tool.name for tool in client.tools]:
            matching_client = client
            break
    if matching_client is None:
        raise ValueError(f'No matching MCP agent found for tool name: {action.name}')
    args_dict = json.loads(action.arguments) if action.arguments else {}
    try:
        response = await matching_client.call_tool(action.name, args_dict)

        if response.isError:
            return ErrorObservation(f'MCP {action.name} failed: {response.content}')
        logger.debug(f'MCP response: {response}')

        # special case for browser screenshot of playwright_mcp
        if (
            matching_client.name == ObservationType.BROWSER_MCP
            and response.content
            and len(response.content) > 0
        ):
            return process_browser_mcp_response(action, response)
        if (
            action.name == 'create_plan'
            or action.name == 'update_plan'
            or action.name == 'get_current_plan'
        ):
            # Handle the case where the response is not empty
            return planner_mcp_plan(action, response)
        if action.name == 'pyodide_execute_python' and len(response.content) > 0:
            return pyodide_mcp_response(action, response)

        return MCPObservation(content=f'{response.content[0].text}')
    except Exception as e:
        logger.error(f'Error calling tool {action.name}: {e}')
        return ErrorObservation(f'MCP {action.name} failed: {e}')


def extract_page_url(browser_content: str) -> str | Any:
    # Regex to find the line starting with "- Page URL:" and capture the URL
    # Explanation:
    # ^                - Matches the start of a line (due to re.MULTILINE)
    # \s*              - Matches optional leading whitespace
    # - Page URL:      - Matches the literal string
    # \s+              - Matches one or more whitespace characters after the colon
    # (https?://[^\s]+) - Captures the URL (starts with http/https, followed by non-whitespace chars)
    pattern = re.compile(r'^\s*- Page URL:\s+(https?://[^\s]+)', re.MULTILINE)
    match = pattern.search(browser_content)
    page_url = ''
    if match:
        page_url = match.group(1)  # group(1) is the captured URL
    return page_url


def process_browser_mcp_response(
    action: McpAction, browser_response: CallToolResult
) -> Observation:
    browser_content = browser_response.content
    text_content: TextContent = browser_content[0]
    image_content: ImageContent | None = None
    if len(browser_content) > 1:
        image_content = browser_content[1]

    # logger.debug(f'image_content: {image_content}')
    # logger.debug(f'text_content: {text_content}')
    url = extract_page_url(text_content.text) if text_content else ''

    # logger.debug(f'Screenshot content: {screenshot_content}')
    return BrowserMCPObservation(
        content=f'{text_content.text}',
        url=url,
        trigger_by_action=action.name,
        screenshot=f'data:image/png;base64,{image_content.data}'
        if image_content is not None
        else '',
    )


def planner_mcp_plan(_: McpAction, response: CallToolResult) -> Observation:
    logger.info(f'Planner MCP response: {response.content}')
    if len(response.content) == 0 or not isinstance(response.content[0], TextContent):
        return ErrorObservation(
            f'Planner MCP response is empty or not text content: {response.content}'
        )

    resonpse_dict = json.loads(response.content[0].text)
    observation = PlanObservation(
        plan_id=resonpse_dict['plan_id'],
        tasks=[
            {
                'content': task['content'],
                'status': task['status'],
                'result': task['result'],
            }
            for task in resonpse_dict['tasks']
        ],
        title=resonpse_dict['title'],
        content=resonpse_dict['title'],
    )

    logger.info(f'Planner MCP observation: {observation}')
    return observation


def pyodide_mcp_response(action: McpAction, response: CallToolResult) -> Observation:
    code = response.content[0].text
    content = response.content[1].text
    if len(response.content) == 0 or not isinstance(response.content[0], TextContent):
        return ErrorObservation(
            f'Pyodide MCP response is empty or not text content: {response.content}'
        )
    return IPythonRunCellObservation(code=code, content=content)
