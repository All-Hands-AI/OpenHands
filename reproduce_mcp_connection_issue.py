#!/usr/bin/env python3
"""
Reproduction script for issue #9030: "No matching MCP agent found for tool name: tavily_tavily-search"

This script focuses specifically on the connection management aspect of the MCP client.
It creates a new MCP client for each search, simulating how the actual code behaves,
and monitors for connection-related issues.

Usage:
    python reproduce_mcp_connection_issue.py [--num-searches NUM_SEARCHES] [--api-key API_KEY]

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


async def create_tavily_mcp_client(api_key: str) -> list[MCPClient]:
    """
    Create a new MCP client for the Tavily search tool.

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
    logger.info('Creating new MCP client...')
    mcp_clients = await create_mcp_clients([], [])

    if not mcp_clients:
        logger.error('Failed to create MCP client')
        return []

    logger.info(
        f'Created new MCP client with {len(mcp_clients[0].tools) if mcp_clients else 0} tools'
    )
    return mcp_clients


async def perform_tavily_search_with_new_client(
    api_key: str, query: str, search_index: int
) -> dict:
    """
    Perform a Tavily search using a new MCP client for each search.
    This simulates how the actual code behaves, creating a new connection for each tool call.

    Args:
        api_key: Tavily API key
        query: Search query
        search_index: Index of the current search (for logging)

    Returns:
        Dictionary with search results and metrics
    """
    result = {
        'success': False,
        'error': None,
        'client_creation_time': 0,
        'search_time': 0,
        'total_time': 0,
        'num_tools': 0,
    }

    start_total = time.time()

    try:
        # Create a new MCP client for each search
        start_client = time.time()
        mcp_clients = await create_tavily_mcp_client(api_key)
        end_client = time.time()
        result['client_creation_time'] = end_client - start_client

        if not mcp_clients:
            result['error'] = 'Failed to create MCP client'
            return result

        result['num_tools'] = len(mcp_clients[0].tools)

        # Create an MCPAction for the Tavily search
        action = MCPAction(
            name='tavily_tavily-search',
            arguments={'query': query},
            thought=f'Search {search_index}: {query}',
        )

        # Call the tool
        logger.info(f'Performing search {search_index}: {query}')
        start_search = time.time()
        await call_tool_mcp(mcp_clients, action)
        end_search = time.time()
        result['search_time'] = end_search - start_search

        logger.info(
            f'Search {search_index} completed in {result["search_time"]:.2f} seconds'
        )
        result['success'] = True
    except Exception as e:
        logger.error(f'Error in search {search_index}: {e}')
        result['error'] = str(e)

    end_total = time.time()
    result['total_time'] = end_total - start_total

    return result


async def main(num_searches: int, api_key: str) -> None:
    """
    Main function to reproduce the issue.

    Args:
        num_searches: Number of consecutive searches to perform
        api_key: Tavily API key
    """
    # Perform consecutive searches with new clients
    search_queries = [
        f'What is the capital of country {i}?' for i in range(1, num_searches + 1)
    ]

    results = []

    for i, query in enumerate(search_queries):
        logger.info(f'Starting search {i + 1}/{num_searches}')
        result = await perform_tavily_search_with_new_client(api_key, query, i + 1)
        results.append(result)

        # Log the result
        if result['success']:
            logger.info(
                f'Search {i + 1} succeeded in {result["total_time"]:.2f}s (client: {result["client_creation_time"]:.2f}s, search: {result["search_time"]:.2f}s)'
            )
        else:
            logger.error(f'Search {i + 1} failed: {result["error"]}')

        # Add a small delay between searches
        await asyncio.sleep(0.5)

    # Analyze the results
    success_count = sum(1 for r in results if r['success'])
    failure_count = len(results) - success_count

    logger.info(f'\nCompleted {num_searches} searches')
    logger.info(f'Success: {success_count}, Failure: {failure_count}')

    if failure_count > 0:
        logger.info('Issue reproduced: Some searches failed')

        # Check for specific errors
        no_matching_agent_errors = sum(
            1
            for r in results
            if r['error'] and 'No matching MCP agent found for tool name' in r['error']
        )
        if no_matching_agent_errors > 0:
            logger.info(
                f"Issue #9030 reproduced: {no_matching_agent_errors} 'No matching MCP agent found for tool name' errors"
            )

        # Analyze when failures started occurring
        first_failure_index = next(
            (i for i, r in enumerate(results) if not r['success']), None
        )
        if first_failure_index is not None:
            logger.info(f'First failure occurred at search {first_failure_index + 1}')
    else:
        logger.info('All searches completed successfully, issue not reproduced')

    # Analyze timing trends
    if results:
        client_times = [r['client_creation_time'] for r in results if r['success']]
        search_times = [r['search_time'] for r in results if r['success']]
        total_times = [r['total_time'] for r in results if r['success']]

        if client_times:
            logger.info('\nTiming analysis (successful searches only):')
            logger.info(
                f'Client creation time: avg={sum(client_times) / len(client_times):.2f}s, min={min(client_times):.2f}s, max={max(client_times):.2f}s'
            )
            logger.info(
                f'Search time: avg={sum(search_times) / len(search_times):.2f}s, min={min(search_times):.2f}s, max={max(search_times):.2f}s'
            )
            logger.info(
                f'Total time: avg={sum(total_times) / len(total_times):.2f}s, min={min(total_times):.2f}s, max={max(total_times):.2f}s'
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reproduce MCP connection issue')
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
