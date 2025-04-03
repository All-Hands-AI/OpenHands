"""
CodeActReadOnlyAgent - A specialized version of CodeActAgent that only uses read-only tools.
"""

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.function_calling import get_tools
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent
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
        # Force codeact_enable_read_only_tools to True to ensure we only get read-only tools
        self.tools = get_tools(
            codeact_enable_browsing=True,  # Enable web_read
            codeact_enable_jupyter=False,
            codeact_enable_llm_editor=False,
            codeact_enable_read_only_tools=True,  # Force read-only mode
            llm=self.llm,
        )

        logger.debug(
            f"TOOLS loaded for CodeActReadOnlyAgent: {', '.join([tool.get('function').get('name') for tool in self.tools])}"
        )

    def _enhance_messages(self, messages: list[Message]) -> list[Message]:
        """Enhance the messages with a note about read-only mode.

        This overrides the parent method to add a note about read-only mode to the system message.

        Parameters:
        - messages (list[Message]): The messages to enhance

        Returns:
        - list[Message]: The enhanced messages
        """
        # First call the parent method to get the base enhanced messages
        enhanced_messages = super()._enhance_messages(messages)

        # Add a note about read-only mode to the system message
        if enhanced_messages and enhanced_messages[0].role == 'system':
            read_only_note = (
                "\n\n[IMPORTANT: You are running in READ-ONLY MODE. You can only use tools that don't modify the system: "
                'grep, glob, view, think, finish, web_read. If you need to make changes, the user must switch to Execute Mode.]'
            )

            # Add the note to the first text content of the system message
            if enhanced_messages[0].content and isinstance(
                enhanced_messages[0].content[0], TextContent
            ):
                enhanced_messages[0].content[0].text += read_only_note

        return enhanced_messages
