"""ReadOnlyPlanningAgent - A specialized planning agent for read-only research plus maintaining PLAN.md.

This agent is derived from CodeActAgent and constrained to:
- Use read-only research tools (grep, glob, view) to explore the repository
- Maintain a single planning document at /workspace/PLAN.md via a dedicated plan editor tool
- Avoid any other code execution or edits outside PLAN.md
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litellm import ChatCompletionToolParam

    from openhands.events.action import Action
    from openhands.llm.llm import ModelResponse

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.readonly_agent import (
    function_calling as readonly_function_calling,
)
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.utils.prompt import PromptManager


class ReadOnlyPlanningAgent(CodeActAgent):
    VERSION = '1.0'
    """
    The ReadOnlyPlanningAgent is designed for planning large features safely.
    It provides:
    - Read-only repo exploration: grep, glob, view
    - PLAN.md maintenance via a specialized plan editor tool (create/view/edit only)
    - No other file modifications or command execution
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
        # Initialize the CodeActAgent class; some of it is overridden with class methods
        super().__init__(llm, config)

        logger.debug(
            f'TOOLS loaded for ReadOnlyPlanningAgent: {", ".join([tool.get("function").get("name") for tool in self.tools])}'
        )

    @property
    def prompt_manager(self) -> PromptManager:
        # Set up our own prompt manager
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(
                prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
            )
        return self._prompt_manager

    def _get_tools(self) -> list['ChatCompletionToolParam']:
        # Override the tools to only include read-only tools
        # Get the read-only tools from our own function_calling module
        return readonly_function_calling.get_tools()

    def set_mcp_tools(self, mcp_tools: list[dict]) -> None:
        """Sets the list of MCP tools for the agent.

        Args:
        - mcp_tools (list[dict]): The list of MCP tools.
        """
        logger.warning(
            'ReadOnlyPlanningAgent does not support MCP tools. MCP tools will be ignored by the agent.'
        )

    def response_to_actions(self, response: 'ModelResponse') -> list['Action']:
        return readonly_function_calling.response_to_actions(
            response, mcp_tool_names=list(self.mcp_tools.keys())
        )
