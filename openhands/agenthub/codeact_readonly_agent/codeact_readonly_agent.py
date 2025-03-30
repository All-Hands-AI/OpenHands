"""
CodeActReadOnlyAgent - A specialized version of CodeActAgent that only uses read-only tools.
"""

import os
from collections import deque

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.tools import (
    FinishTool,
    GlobTool,
    GrepTool,
    ThinkTool,
    ViewTool,
    WebReadTool,
)
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


class CodeActReadOnlyAgent(CodeActAgent):
    VERSION = '1.0'
    """
    The CodeActReadOnlyAgent is a specialized version of CodeActAgent that only uses read-only tools.
    
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
        """Initializes a new instance of the CodeActReadOnlyAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        - config (AgentConfig): The configuration for this agent
        """
        super().__init__(llm, config)
        
        # Override the tools with only read-only tools
        self.tools = [
            ThinkTool,
            ViewTool,
            GrepTool,
            GlobTool,
            FinishTool,
            WebReadTool,
        ]
        
        logger.debug(
            f"TOOLS loaded for CodeActReadOnlyAgent: {', '.join([tool.get('function').get('name') for tool in self.tools])}"
        )

    def get_system_prompt(self, state: State) -> str:
        """Get the system prompt for the agent.
        
        This overrides the parent method to add a note about read-only mode.
        
        Parameters:
        - state (State): The current state of the agent
        
        Returns:
        - str: The system prompt
        """
        original_prompt = super().get_system_prompt(state)
        
        # Add a note about read-only mode
        read_only_note = (
            "\n\n[IMPORTANT: You are running in READ-ONLY MODE. You can only use tools that don't modify the system: "
            "grep, glob, view, think, finish, web_read. If you need to make changes, the user must switch to Execute Mode.]"
        )
        
        return original_prompt + read_only_note