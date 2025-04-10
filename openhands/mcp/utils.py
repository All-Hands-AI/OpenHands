import json
import re
from typing import Any, Optional

from mcp.types import CallToolResult, ImageContent, TextContent

from openhands.core.config.mcp_config import MCPConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.observation import ObservationType
from openhands.events.action.mcp import McpAction
from openhands.events.observation.mcp import MCPObservation
from openhands.events.observation.observation import Observation
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


async def create_mcp_clients(
    dict_mcp_config: dict[str, MCPConfig],
    sid: Optional[str] = None,
    mnemonic: Optional[str] = None,
) -> list[MCPClient]:
    mcp_clients: list[MCPClient] = []
    # Initialize SSE connections
    for name, mcp_config in dict_mcp_config.items():
        logger.info(
            f'Initializing MCP {name} agent for {mcp_config.url} with {mcp_config.mode} connection...'
        )
        client = MCPClient(name=name)
        try:
            await client.connect_sse(mcp_config.url, sid, mnemonic)
            # Only add the client to the list after a successful connection
            mcp_clients.append(client)
            logger.info(f'Connected to MCP server {mcp_config.url} via SSE')
        except Exception as e:
            logger.error(f'Failed to connect to {mcp_config.url}: {str(e)}')
            try:
                await client.disconnect()
            except Exception as disconnect_error:
                logger.error(
                    f'Error during disconnect after failed connection: {str(disconnect_error)}'
                )

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
        for mcp_client in mcp_clients:
            try:
                await mcp_client.disconnect()
            except Exception as disconnect_error:
                logger.error(f'Error disconnecting MCP client: {str(disconnect_error)}')
    except Exception as e:
        logger.error(f'Error fetching MCP tools: {str(e)}')
        return []

    logger.debug(f'MCP tools: {mcp_tools}')
    return mcp_tools


async def call_tool_mcp(mcp_clients: list[MCPClient], action: McpAction) -> Observation:
    """
    Call a tool on an MCP server and return the observation.

    Args:
        mcp_clients: List of MCPClient instances
        action: The MCP action to execute

    Returns:
        The observation from the MCP server
    """
    if not mcp_clients:
        raise ValueError('No MCP clients found')

    logger.debug(f'MCP action received: {action}')
    # Find the MCP agent that has the matching tool name
    matching_client = None
    logger.debug(f'MCP clients: {mcp_clients}')
    logger.debug(f'MCP action name: {action.name}')
    for client in mcp_clients:
        logger.debug(f'MCP client tools: {client.tools}')
        if action.name in [tool.name for tool in client.tools]:
            matching_client = client
            break
    if matching_client is None:
        raise ValueError(f'No matching MCP agent found for tool name: {action.name}')
    logger.debug(f'Matching client: {matching_client}')
    args_dict = json.loads(action.arguments) if action.arguments else {}
    response = await matching_client.call_tool(action.name, args_dict)
    logger.debug(f'MCP response: {response}')

    # special case for browser screenshot of playwright_mcp
    if (
        matching_client.name == ObservationType.BROWSER_MCP
        and response.content
        and len(response.content) > 0
    ):
        return process_browser_mcp_response(action, response)

    return MCPObservation(
        content=f'MCP {action.name} result: {response.model_dump(mode="json")}'
    )


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

    logger.debug(f'image_content: {image_content}')
    logger.debug(f'text_content: {text_content}')
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
