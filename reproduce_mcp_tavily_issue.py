#!/usr/bin/env python3
"""
Reproduction script for issue #9030: "No matching MCP agent found for tool name: tavily_tavily-search"

This script attempts to reproduce the issue by making multiple consecutive calls to the
tavily_tavily-search tool through the MCP client. It monitors for any errors, especially
the "No matching MCP agent found for tool name" error.

Usage:
    python reproduce_mcp_tavily_issue.py [--num-searches NUM_SEARCHES] [--api-key API_KEY]

Arguments:
    --num-searches: Number of consecutive searches to perform (default: 50)
    --api-key: Tavily API key (required if not set in environment)
"""

import argparse
import asyncio
import os
import sys
import time

# Add the OpenHands directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import MCPAction
from openhands.mcp.client import MCPClient
from openhands.mcp.utils import call_tool_mcp, create_mcp_clients


async def setup_tavily_mcp_client(api_key: str) -> list[MCPClient]:
    """
    Set up an MCP client for the Tavily search tool.

    Args:
        api_key: Tavily API key

    Returns:
        List of MCPClient instances
    """
    # Create a Tavily stdio server config
    tavily_server = MCPStdioServerConfig(
        name='tavily',
        command='npx',
        args=['-y', 'tavily-mcp@0.2.1'],
        env={'TAVILY_API_KEY': api_key},
    )

    # Create an MCP config with the Tavily server
    MCPConfig(stdio_servers=[tavily_server])

    # Create MCP clients
    logger.info('Creating MCP clients...')
    mcp_clients = await create_mcp_clients([], [])

    if not mcp_clients:
        logger.error('Failed to create MCP clients')
        return []

    logger.info(f'Created {len(mcp_clients)} MCP clients')
    return mcp_clients


async def perform_tavily_search(
    mcp_clients: list[MCPClient], query: str, search_index: int
) -> bool:
    """
    Perform a Tavily search using the MCP client.

    Args:
        mcp_clients: List of MCPClient instances
        query: Search query
        search_index: Index of the current search (for logging)

    Returns:
        True if the search was successful, False otherwise
    """
    try:
        # Create an MCPAction for the Tavily search
        action = MCPAction(
            name='tavily_tavily-search',
            arguments={'query': query},
            thought=f'Search {search_index}: {query}',
        )

        # Call the tool
        logger.info(f'Performing search {search_index}: {query}')
        start_time = time.time()
        await call_tool_mcp(mcp_clients, action)
        end_time = time.time()

        logger.info(
            f'Search {search_index} completed in {end_time - start_time:.2f} seconds'
        )
        return True
    except Exception as e:
        logger.error(f'Error in search {search_index}: {e}')
        return False


async def monitor_connections(mcp_clients: list[MCPClient]) -> None:
    """
    Monitor the MCP client connections and log their status.

    Args:
        mcp_clients: List of MCPClient instances
    """
    while True:
        for i, client in enumerate(mcp_clients):
            logger.info(f'Client {i}: {len(client.tools)} tools available')
            for tool in client.tools:
                logger.info(f'  - {tool.name}')

        await asyncio.sleep(5)


async def main(num_searches: int, api_key: str) -> None:
    """
    Main function to reproduce the issue.

    Args:
        num_searches: Number of consecutive searches to perform
        api_key: Tavily API key
    """
    # Set up the MCP client
    mcp_clients = await setup_tavily_mcp_client(api_key)

    if not mcp_clients:
        logger.error('Failed to set up MCP clients, exiting')
        return

    # Start the connection monitor in the background
    monitor_task = asyncio.create_task(monitor_connections(mcp_clients))

    # Perform consecutive searches
    search_queries = [
        f'What is the capital of country {i}?' for i in range(1, num_searches + 1)
    ]

    success_count = 0
    failure_count = 0

    for i, query in enumerate(search_queries):
        success = await perform_tavily_search(mcp_clients, query, i + 1)

        if success:
            success_count += 1
        else:
            failure_count += 1

        # Add a small delay between searches to avoid overwhelming the server
        await asyncio.sleep(0.5)

    # Cancel the monitor task
    monitor_task.cancel()

    # Log the results
    logger.info(f'Completed {num_searches} searches')
    logger.info(f'Success: {success_count}, Failure: {failure_count}')

    if failure_count > 0:
        logger.info('Issue reproduced: Some searches failed')

        # Check if the specific error occurred
        if any(
            'No matching MCP agent found for tool name' in str(e)
            for e in logger.handlers[0].records
        ):
            logger.info(
                "Issue #9030 reproduced: 'No matching MCP agent found for tool name: tavily_tavily-search'"
            )
    else:
        logger.info('All searches completed successfully, issue not reproduced')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reproduce MCP Tavily issue')
    parser.add_argument(
        '--num-searches',
        type=int,
        default=50,
        help='Number of consecutive searches to perform',
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('TAVILY_API_KEY'),
        help='Tavily API key',
    )

    args = parser.parse_args()

    if not args.api_key:
        print(
            'Error: Tavily API key is required. Set it with --api-key or TAVILY_API_KEY environment variable.'
        )
        sys.exit(1)

    asyncio.run(main(args.num_searches, args.api_key))
