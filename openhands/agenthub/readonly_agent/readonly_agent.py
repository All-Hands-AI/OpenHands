"""
ReadOnlyAgent - A specialized version of CodeActAgent that only uses read-only tools.
"""

import os
from collections import deque

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.readonly_agent import function_calling as readonly_function_calling
from openhands.core.action import Action
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message, TextContent, ContentType
from openhands.llm.llm import LLM
from openhands.prompt.prompt_manager import PromptManager


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
        # Initialize the base class but we'll override some of its behavior
        super().__init__(llm, config)
        
        # Reset the pending actions queue
        self.pending_actions = deque()
        self.reset()
        
        # Get the read-only tools from our own function_calling module
        self.tools = readonly_function_calling.get_tools(
            enable_browsing=self.config.enable_browsing,
            llm=self.llm,
        )
        
        # Set up our own prompt manager
        self.prompt_manager = PromptManager(
            prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
        )

        logger.debug(
            f"TOOLS loaded for ReadOnlyAgent: {', '.join([tool.get('function').get('name') for tool in self.tools])}"
        )
        
    def process_action(self, action: Action) -> Message:
        """Process an action and return a message.
        
        This method overrides the CodeActAgent's process_action method to ensure
        that only read-only actions are processed.
        
        Parameters:
        - action: The action to process
        
        Returns:
        - A message containing the result of the action
        """
        # Check if the action is a read-only action
        if action.__class__.__name__ not in [
            'ThinkAction',
            'ViewAction',
            'GrepAction',
            'GlobAction',
            'FinishAction',
            'WebReadAction',
        ]:
            # Return an error message if the action is not read-only
            return Message(
                role='assistant',
                content=TextContent(
                    text=f"Error: ReadOnlyAgent cannot process action of type {action.__class__.__name__}. "
                    f"Only read-only actions are allowed."
                ),
            )
        
        # Process the action using the parent class's method
        return super().process_action(action)

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