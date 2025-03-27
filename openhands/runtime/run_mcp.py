#!/usr/bin/env python
import argparse
import asyncio
import sys
from typing import List

from openhands.agenthub.codeact_agent.tools.mcp_agent import MCPAgent
from openhands.core.config.app_config import AppConfig
from openhands.core.config.utils import get_parser, setup_config_from_args
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
from openhands.llm.llm import LLM


class MCPRunner:
    """Runner class for MCP Agent with proper path handling and configuration."""

    def __init__(self, config: AppConfig):
        self.server_reference = 'openhands.agenthub.codeact_agent.tools.mcp_agent'
        llm_config = config.get_llm_config_from_agent(config.default_agent)
        self.config = config
        self.llm = LLM(config=llm_config)
        self.mcp_agents: List[MCPAgent] = []

    async def initialize(self) -> None:
        """Initialize the MCP agent with multiple connections based on config."""
        if not hasattr(self.config, 'mcp'):
            logger.error('MCP configuration not found')
            return

        mcp_config = self.config.mcp

        # Initialize SSE connections
        if mcp_config.sse.mcp_servers:
            for server_url in mcp_config.sse.mcp_servers:
                logger.info(
                    f'Initializing MCP agent for {server_url} with SSE connection...'
                )

                agent = MCPAgent()
                try:
                    await agent.initialize(connection_type='sse', server_url=server_url)
                    self.mcp_agents.append(agent)
                    logger.info(f'Connected to MCP server {server_url} via SSE')
                except Exception as e:
                    logger.error(f'Failed to connect to {server_url}: {str(e)}')
                    raise

        # Initialize stdio connections
        if mcp_config.stdio.commands:
            for command, args in zip(mcp_config.stdio.commands, mcp_config.stdio.args):
                logger.info(
                    f'Initializing MCP agent for {command} with stdio connection...'
                )

                agent = MCPAgent()
                try:
                    await agent.initialize(
                        connection_type='stdio', command=command, args=args
                    )
                    self.mcp_agents.append(agent)
                    logger.info(
                        f'Connected to MCP server via stdio with command {command}'
                    )
                except Exception as e:
                    logger.error(f'Failed to connect with command {command}: {str(e)}')
                    raise

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
        for agent in self.mcp_agents:
            await agent.cleanup()
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
        if args.prompt:
            await runner.run_single_prompt(args.prompt)

    except KeyboardInterrupt:
        logger.info('Program interrupted by user')
    except Exception as e:
        logger.error(f'Error running MCPAgent: {str(e)}', exc_info=True)
        sys.exit(1)
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(run_mcp())
