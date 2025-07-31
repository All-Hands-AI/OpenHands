#!/usr/bin/env python
import argparse
import sys
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from openhands.core.config.app_config import AppConfig
from openhands.core.config.utils import get_parser, setup_config_from_args
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.llm.llm import LLM
from openhands.mcp import MCPClient, convert_mcp_clients_to_tools


class MCPRunner:
    """Runner class for MCP Agent with proper path handling and configuration."""

    def __init__(self, config: AppConfig):
        self.server_reference = 'openhands.mcp.mcp_agent'
        llm_config = config.get_llm_config_from_agent(config.default_agent)
        self.config = config
        self.llm = LLM(config=llm_config)
        self.mcp_clients: List[MCPClient] = []

    async def initialize(self) -> None:
        """Initialize the MCP agent with multiple connections based on config."""

        mcp_config = self.config.dict_mcp_config

        # Initialize SSE connections
        if mcp_config:
            for name, config_dict in mcp_config.items():
                logger.info(f'Initializing MCP agent for {name} with SSE connection...')

                client = MCPClient()
                try:
                    await client.connect_sse(server_url=config_dict['url'])
                    self.mcp_clients.append(client)
                    logger.info(f'Connected to MCP server {config_dict["url"]} via SSE')
                except Exception as e:
                    logger.error(f'Failed to connect to {config_dict["url"]}: {str(e)}')
                    raise

        mcp_tools = convert_mcp_clients_to_tools(self.mcp_clients)
        logger.info(f'MCP tools: {mcp_tools}')

        for client in self.mcp_clients:
            is_connected = client._is_connected()
            assert is_connected
            logger.info(f'Is connected: {is_connected}')

    async def run_single_prompt(self, prompt: str) -> None:
        """Run the agent with a single prompt."""
        logger.info(f'Running MCP agent with prompt: {prompt}')
        messages: list[Message] = [
            Message(role='user', content=[TextContent(text=prompt)])
        ]
        response = self.llm.completion(
            messages=self.llm.format_messages_for_llm(messages),
        )
        print('response: ', response)
        return response

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        for client in self.mcp_clients:
            await client.disconnect()
        logger.info('Session ended')


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = get_parser()
    parser.add_argument('--prompt', '-p', help='Single prompt to execute and exit')
    return parser.parse_args()


async def run_mcp() -> None:
    """Main entry point for the MCP runner."""
    args = parse_args()

    config: AppConfig = setup_config_from_args(args)
    runner = MCPRunner(config)

    try:
        await runner.initialize()

    except KeyboardInterrupt:
        logger.info('Program interrupted by user')
    except Exception as e:
        logger.error(f'Error running MCPRunner: {str(e)}', exc_info=True)
        sys.exit(1)
    finally:
        await runner.cleanup()


# Test the MCPRunner with mocked connect_sse and is_connected
@pytest.mark.asyncio
async def test_mcp_runner():
    """Test MCPRunner with mocked connect_sse and is_connected."""
    # Create a mock config
    config = AppConfig()
    config.default_agent = 'test_agent'
    config.dict_mcp_config = {'test_mcp': {'url': 'http://test-url'}}

    # Create MCPRunner instance
    runner = MCPRunner(config)

    # Mock MCPClient's connect_sse and is_connected methods
    with patch.object(
        MCPClient, 'connect_sse', new_callable=AsyncMock
    ) as mock_connect_sse, patch.object(
        MCPClient, '_is_connected', new_callable=AsyncMock, return_value=True
    ) as mock_is_connected:
        # Run initialization
        await runner.initialize()

        # Verify connect_sse was called with the correct URL
        mock_connect_sse.assert_called_once_with(server_url='http://test-url')

        # Verify is_connected was called
        mock_is_connected.assert_called_once()

        # Verify client was added to mcp_clients list
        assert len(runner.mcp_clients) == 1
