#!/usr/bin/env python
import argparse
import asyncio
import sys

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
        self.agent = MCPAgent()
        llm_config = config.get_llm_config_from_agent(config.default_agent)
        self.config = config.get_agent_config(config.default_agent)
        self.llm = LLM(config=llm_config)

    async def initialize(
        self,
        connection_type: str,
        server_url: str | None = None,
    ) -> None:
        """Initialize the MCP agent with the appropriate connection."""
        logger.info(f'Initializing MCPAgent with {connection_type} connection...')

        if connection_type == 'stdio':
            await self.agent.initialize(
                connection_type='stdio',
                command=sys.executable,
                args=['-m', self.server_reference],
            )
        else:  # sse
            await self.agent.initialize(connection_type='sse', server_url=server_url)

        logger.info(f'Connected to MCP server via {connection_type}')

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
        await self.agent.cleanup()
        logger.info('Session ended')


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = get_parser()
    parser.add_argument(
        '--mcp-connection',
        choices=['stdio', 'sse'],
        default='sse',
        help='Connection type: stdio or sse',
    )
    parser.add_argument(
        '--mcp-server-url',
        default='http://127.0.0.1:8000/sse',
        help='URL for SSE connection',
    )
    parser.add_argument('--prompt', '-p', help='Single prompt to execute and exit')
    return parser.parse_args()


async def run_mcp() -> None:
    """Main entry point for the MCP runner."""
    args = parse_args()

    config: AppConfig = setup_config_from_args(args)
    runner = MCPRunner(config)

    try:
        await runner.initialize(args.mcp_connection, args.mcp_server_url)
        # await runner.run_single_prompt(args.prompt)

    except KeyboardInterrupt:
        logger.info('Program interrupted by user')
    except Exception as e:
        logger.error(f'Error running MCPAgent: {str(e)}', exc_info=True)
        sys.exit(1)
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(run_mcp())
