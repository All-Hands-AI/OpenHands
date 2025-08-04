"""TomCodeActAgent: CodeAct Agent enhanced with Tom agent integration."""

import asyncio
import os
from collections import deque
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from openhands.events.action import Action

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.tom_codeact_agent.tom_config import TomCodeActAgentConfig
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.events.action import AgentFinishAction, MessageAction
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.llm.llm_utils import check_tools
from openhands.memory.condenser.condenser import Condensation, View
from openhands.utils.prompt import PromptManager

from tom_swe.tom_agent import create_tom_agent


class TomCodeActAgent(CodeActAgent):
    """CodeAct Agent enhanced with Tom agent integration.

    This agent extends CodeActAgent to provide personalized guidance through
    the Tom agent at two key integration points:
    1. When a user message is received - improve the instruction
    2. When the agent finishes a task - suggest next actions
    """

    VERSION = '1.0'
    config_model = TomCodeActAgentConfig

    def __init__(self, llm: LLM, config: AgentConfig) -> None:
        """Initialize TomCodeActAgent.

        Args:
            llm: Language model to use
            config: Agent configuration (will be converted to TomCodeActAgentConfig if needed)
        """
        super().__init__(llm, config)

        # Convert config to TomCodeActAgentConfig if it's not already
        if not isinstance(config, TomCodeActAgentConfig):
            # Get base config dict and add Tom-specific defaults only if not present
            base_config = config.model_dump()
            tom_defaults = {
                'enable_tom_integration': True,
                'tom_processed_data_dir': "./data/processed_data",
                'tom_user_model_dir': "./data/user_model",
                'tom_enable_rag': False,
                'tom_user_id': None,
                'tom_fallback_on_error': True,
                'tom_min_instruction_length': 5
            }
            # Only add Tom config if not already present
            for key, value in tom_defaults.items():
                if key not in base_config:
                    base_config[key] = value

            tom_config = TomCodeActAgentConfig(**base_config)
        else:
            tom_config = config

        # Tom integration components
        self.tom_config = tom_config
        self.tom_agent = create_tom_agent(
            processed_data_dir=self.tom_config.tom_processed_data_dir,
            user_model_dir=self.tom_config.tom_user_model_dir,
            enable_rag=self.tom_config.tom_enable_rag,
            llm_model=llm.config.model,
            api_key=llm.config.api_key.get_secret_value() if llm.config.api_key else None,
            api_base=llm.config.base_url,
        )
        self.tom_enabled = tom_config.enable_tom_integration
        self._last_processed_user_message_id: Optional[int] = None

        logger.info(f"TomCodeActAgent initialized with Tom integration: {self.tom_enabled}")
        if self.tom_enabled:
            logger.info(f"Tom processed data dir: {tom_config.tom_processed_data_dir}")
            logger.info(f"Tom user model dir: {tom_config.tom_user_model_dir}")

    @property
    def prompt_manager(self) -> PromptManager:
        """Get the prompt manager, using tom_codeact_agent prompts."""
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(
                prompt_dir=os.path.join(os.path.dirname(__file__), 'prompts'),
                system_prompt_filename=self.config.system_prompt_filename,
            )
        return self._prompt_manager

    def step(self, state: State) -> 'Action':
        """Enhanced step method with Tom integration at two key points.

        This method follows the same flow as CodeActAgent but adds Tom integration:
        1. Before processing - check for instruction improvements
        2. After processing - check for next action suggestions when finishing

        Args:
            state: Current agent state

        Returns:
            Action to execute next
        """
        # Continue with pending actions first
        if self.pending_actions:
            return self.pending_actions.popleft()
        # Handle exit command
        latest_user_message = state.get_last_user_message()
        if latest_user_message and latest_user_message.content.strip() == '/exit':
            return AgentFinishAction()

        # Get condensed history and messages (same as CodeAct)
        condensed_history: list[Event] = []
        match self.condenser.condensed_history(state):
            case View(events=events):
                condensed_history = events
            case Condensation(action=condensation_action):
                return condensation_action

        logger.debug(
            f'Processing {len(condensed_history)} events from a total of {len(state.history)} events'
        )

        initial_user_message = self._get_initial_user_message(state.history)
        messages = self._get_messages(condensed_history, initial_user_message)
        formatted_messages = self.llm.format_messages_for_llm(messages)

        # INTEGRATION POINT 1: Improve instruction when new user message received

        if (self.tom_enabled and
            latest_user_message and
            self._is_new_user_message(latest_user_message)):

            logger.info(f"🚀 Tom: Integration Point 1 triggered - improving user instruction")
            try:
                enhanced_instruction = self._improve_instruction_with_tom(latest_user_message, formatted_messages, state)
                if enhanced_instruction:
                    logger.info(f"✅ Tom: Using Tom's enhanced instruction")
                    # Update the formatted messages with the enhanced instruction
                    formatted_messages = self._update_messages_with_enhanced_understanding(formatted_messages, enhanced_instruction)
                    # Mark this message as processed
                    self._last_processed_user_message_id = id(latest_user_message)
                else:
                    logger.info(f"➡️ Tom: No improvement provided, continuing with original instruction")
            except Exception as e:
                logger.error(f"❌ Tom: Error in instruction improvement: {e}")
                logger.info(f"➡️ Tom: Falling back to original instruction due to error")
        # Continue with normal CodeAct processing
        params: dict = {
            'messages': formatted_messages,
        }
        params['tools'] = check_tools(self.tools, self.llm.config)
        params['extra_body'] = {'metadata': state.to_llm_metadata(model_name=self.llm.config.model, agent_name=self.name)}
        response = self.llm.completion(**params)
        logger.debug(f'Response from LLM: {response}')
        actions = self.response_to_actions(response)
        logger.debug(f'Actions after response_to_actions: {actions}')

        # INTEGRATION POINT 2: Suggest next actions when agent finishes
        finish_actions = [action for action in actions if isinstance(action, AgentFinishAction)]
        logger.debug(f"🔍 Tom: Integration Point 2 check - tom_enabled: {self.tom_enabled}, finish_actions: {len(finish_actions)}")
        # Queue all actions for execution
        for action in actions:
            self.pending_actions.append(action)

        return self.pending_actions.popleft()

    def _is_new_user_message(self, user_message: MessageAction) -> bool:
        """Check if this is a new user message that should be processed with Tom.

        Args:
            user_message: The user message to check

        Returns:
            True if this is a new user message that should trigger Tom improvement
        """
        source_check = user_message.source == 'user'
        id_check = id(user_message) != self._last_processed_user_message_id
        length_check = len(user_message.content.strip()) >= self.tom_config.tom_min_instruction_length

        logger.debug(f"🔍 Tom: Message checks - source='{user_message.source}' (=='user': {source_check}), id={id(user_message)} (!=last: {id_check}), length={len(user_message.content.strip())} (>={self.tom_config.tom_min_instruction_length}: {length_check})")

        return source_check and id_check and length_check



    def _update_messages_with_enhanced_understanding(self, formatted_messages: list, enhanced_message: str) -> list:
        """Update the formatted messages with enhanced user message understanding.

        Args:
            formatted_messages: Original formatted messages
            enhanced_message: Enhanced user message content

        Returns:
            Updated formatted messages with enhanced understanding
        """
        # Find the last user message and update it
        updated_messages = []
        last_user_message_index = -1

        # Find the index of the last user message
        for i, message in enumerate(formatted_messages):
            if message.get('role') == 'user':
                last_user_message_index = i

        # Update only the last user message
        for i, message in enumerate(formatted_messages):
            if i == last_user_message_index and message.get('role') == 'user':
                # Update the last user message with enhanced understanding
                updated_message = message.copy()
                updated_message['content'] = enhanced_message
                updated_messages.append(updated_message)
            else:
                updated_messages.append(message)

        return updated_messages

    def _improve_instruction_with_tom(
        self, user_message: MessageAction, formatted_messages: list, state: State
    ) -> Optional[str]:
        """INTEGRATION POINT 1: Get instruction improvements from Tom.

        Args:
            user_message: The user message to improve
            formatted_messages: Full conversation context in LLM format
            state: Current agent state

        Returns:
            Enhanced instruction string if improvements are available, None otherwise
        """
        try:
            user_id = state.user_id or 'default_user'
            context = self._extract_context_from_messages(formatted_messages)

            logger.info(f"🔄 Tom: Requesting instruction improvement for user: {user_id}")
            logger.info(f"📝 Tom: Original instruction: {user_message.content}")
            logger.info(f"📋 Tom: Context length: {len(context)} characters")

            # Single synchronous call that includes user context analysis
            improved_instruction = self.tom_agent.propose_instructions(
                user_id=user_id,
                original_instruction=user_message.content,
                user_msg_context=context,
            )
            if improved_instruction:
                logger.info(f"✅ Tom: Received improved instruction")
                logger.info(f"💡 Tom: Improved instruction: {improved_instruction}")
                return improved_instruction.improved_instruction
            else:
                logger.warning(f"⚠️ Tom: No instruction improvements provided")

        except Exception as e:
            logger.error(f"❌ Tom: Instruction improvement failed with exception: {e}")
            if not self.tom_config.tom_fallback_on_error:
                raise
            else:
                logger.warning(f"🔄 Tom: Falling back to original instruction due to error")

        return None

    def _extract_context_from_messages(self, formatted_messages: list) -> str:
        """Extract context from the formatted LLM messages.

        Args:
            formatted_messages: Messages formatted for LLM consumption

        Returns:
            String representation of the conversation context
        """
        context_parts = []

        for message in formatted_messages:  # All messages for context
            role = message.get('role', '')
            content = message.get('content', '')

            # Convert content to string if it's a list (for vision/multi-content messages)
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text_parts.append(item.get('text', ''))
                    else:
                        text_parts.append(str(item))
                content = ' '.join(text_parts)

            # Skip empty content
            if not content.strip():
                continue

            # Format based on role
            if role == 'system':
                context_parts.append(f"System: {content}")
            elif role == 'user':
                context_parts.append(f"User: {content}")
            elif role == 'assistant':
                context_parts.append(f"Assistant: {content}")
            elif role == 'tool':
                context_parts.append(f"Tool: {content}")

        return '\n'.join(context_parts)


    async def __aenter__(self):
        """Async context manager entry."""
        return self
