"""
ReadOnlyAgent - A specialized version of CodeActAgent that only uses read-only tools.
"""

import os

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.readonly_agent import (
    function_calling as readonly_function_calling,
)
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.utils.prompt import PromptManager


class ReadOnlyAgent(CodeActAgent):
    VERSION = '1.0'
    """
    The ReadOnlyAgent is a specialized version of CodeActAgent that only uses read-only tools.

    This agent is designed for safely exploring codebases without making any changes.
    It only has access to tools that don't modify the system: grep, glob, view, think, finish, web_read.

    Use this agent when you want to:
    1. Explore a codebase to understand its structure
    2. Search for specific patterns or code
    3. Research without making any changes

    When you're ready to make changes, switch to the regular CodeActAgent.
    """

    def __init__(
        self,
        llm: LLM,
        config: AgentConfig,
    ) -> None:
        """Initializes a new instance of the ReadOnlyAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        # Initialize the CodeActAgent class but we'll override some of its behavior
        super().__init__(llm, config)

        # Override the tools to only include read-only tools
        # Get the read-only tools from our own function_calling module
        self.tools = readonly_function_calling.get_tools()

        # Set up our own prompt manager
        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )

        self.response_to_actions_fn = readonly_function_calling.response_to_actions

        logger.debug(
            f"TOOLS loaded for ReadOnlyAgent: {', '.join([tool.get('function').get('name') for tool in self.tools])}"
        )

    def set_mcp_tools(self, mcp_tools: list[dict]) -> None:
        """Sets the list of MCP tools for the agent.

        Args:
        - mcp_tools (list[dict]): The list of MCP tools.
        """
        logger.warning(
            'ReadOnlyAgent does not support MCP tools. MCP tools will be ignored by the agent.'
        )
