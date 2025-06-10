#!/usr/bin/env python3
"""
Reproduction script for issue #9030: "No matching MCP agent found for tool name: tavily_tavily-search"

This script focuses on the connection pooling aspect of the MCP client.
It creates a single MCP client and reuses it for multiple searches, monitoring
for connection-related issues and resource leaks.

Usage:
    python reproduce_mcp_connection_pooling.py [--num-searches NUM_SEARCHES] [--api-key API_KEY]

Arguments:
    --num-searches: Number of consecutive searches to perform (default: 50)
    --api-key: Tavily API key (required if not set in environment)
"""

import argparse
import asyncio
import os
import resource
import sys
import time
import tracemalloc

# Add the OpenHands directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openhands.core.config.mcp_config import MCPConfig, MCPStdioServerConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import MCPAction
from openhands.mcp.client import MCPClient
from openhands.mcp.utils import call_tool_mcp, create_mcp_clients


def get_resource_usage() -> dict:
    """
    Get current resource usage statistics.

    Returns:
        Dictionary with resource usage metrics
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        'memory_rss': usage.ru_maxrss,  # Peak resident set size
        'user_time': usage.ru_utime,  # User CPU time
        'system_time': usage.ru_stime,  # System CPU time
        'open_files': len(os.listdir('/proc/self/fd'))
        if os.path.exists('/proc/self/fd')
        else -1,
    }


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

    logger.info(
        f'Created {len(mcp_clients)} MCP clients with {len(mcp_clients[0].tools) if mcp_clients else 0} tools'
    )
    return mcp_clients


async def perform_tavily_search(
    mcp_clients: list[MCPClient], query: str, search_index: int
) -> dict:
    """
    Perform a Tavily search using the MCP client.

    Args:
        mcp_clients: List of MCPClient instances
        query: Search query
        search_index: Index of the current search (for logging)

    Returns:
        Dictionary with search results and metrics
    """
    result = {
        'success': False,
        'error': None,
        'search_time': 0,
        'num_tools': len(mcp_clients[0].tools)
        if mcp_clients and mcp_clients[0].tools
        else 0,
    }

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

        result['search_time'] = end_time - start_time
        logger.info(
            f'Search {search_index} completed in {result["search_time"]:.2f} seconds'
        )
        result['success'] = True
    except Exception as e:
        logger.error(f'Error in search {search_index}: {e}')
        result['error'] = str(e)

    return result


async def main(num_searches: int, api_key: str) -> None:
    """
    Main function to reproduce the issue.

    Args:
        num_searches: Number of consecutive searches to perform
        api_key: Tavily API key
    """
    # Start memory tracking
    tracemalloc.start()

    # Get initial resource usage
    initial_resources = get_resource_usage()
    logger.info(f'Initial resource usage: {initial_resources}')

    # Set up the MCP client (reused for all searches)
    mcp_clients = await setup_tavily_mcp_client(api_key)

    if not mcp_clients:
        logger.error('Failed to set up MCP clients, exiting')
        return

    # Perform consecutive searches
    search_queries = [
        f'What is the capital of country {i}?' for i in range(1, num_searches + 1)
    ]

    results = []
    resource_snapshots = []
    memory_snapshots = []

    for i, query in enumerate(search_queries):
        # Take memory snapshot before search
        current, peak = tracemalloc.get_traced_memory()
        memory_snapshots.append((current, peak))

        # Take resource snapshot
        resource_snapshots.append(get_resource_usage())

        # Perform search
        logger.info(f'Starting search {i + 1}/{num_searches}')
        result = await perform_tavily_search(mcp_clients, query, i + 1)
        results.append(result)

        # Log the result
        if result['success']:
            logger.info(f'Search {i + 1} succeeded in {result["search_time"]:.2f}s')
        else:
            logger.error(f'Search {i + 1} failed: {result["error"]}')

        # Add a small delay between searches
        await asyncio.sleep(0.5)

    # Take final snapshots
    final_resources = get_resource_usage()
    current, peak = tracemalloc.get_traced_memory()
    final_memory = (current, peak)

    # Stop memory tracking
    tracemalloc.stop()

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

    # Analyze resource usage
    logger.info('\nResource usage analysis:')
    logger.info(f'Initial resources: {initial_resources}')
    logger.info(f'Final resources: {final_resources}')
    logger.info(
        f'Memory change: {final_resources["memory_rss"] - initial_resources["memory_rss"]} KB'
    )
    logger.info(
        f'Open files change: {final_resources["open_files"] - initial_resources["open_files"]}'
    )

    # Analyze memory usage
    logger.info('\nMemory tracking:')
    logger.info(
        f'Initial memory: current={memory_snapshots[0][0] / 1024 / 1024:.2f} MB, peak={memory_snapshots[0][1] / 1024 / 1024:.2f} MB'
    )
    logger.info(
        f'Final memory: current={final_memory[0] / 1024 / 1024:.2f} MB, peak={final_memory[1] / 1024 / 1024:.2f} MB'
    )
    logger.info(
        f'Memory growth: {(final_memory[0] - memory_snapshots[0][0]) / 1024 / 1024:.2f} MB'
    )

    # Check for memory leaks
    if final_memory[0] > memory_snapshots[0][0] * 1.5:  # 50% growth threshold
        logger.warning('Potential memory leak detected')

    # Check for file descriptor leaks
    if (
        final_resources['open_files'] > initial_resources['open_files'] * 1.5
    ):  # 50% growth threshold
        logger.warning('Potential file descriptor leak detected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Reproduce MCP connection pooling issue'
    )
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
