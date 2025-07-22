"""TomCodeActAgent: CodeAct Agent enhanced with Tom agent integration."""

import asyncio
import os
from collections import deque
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from openhands.events.action import Action

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.tom_codeact_agent.tom_actions import (
    TomInstructionAction,
    TomSuggestionAction,
)
from openhands.agenthub.tom_codeact_agent.tom_api_client import TomApiClient
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
            # Create TomCodeActAgentConfig with defaults
            tom_config = TomCodeActAgentConfig(
                **config.model_dump(),
                enable_tom_integration=False,  # Default to disabled
                tom_api_url="http://localhost:8000",
                tom_user_id=None,
                tom_timeout=30,
                tom_fallback_on_error=True,
                tom_min_instruction_length=5
            )
        else:
            tom_config = config

        # Tom integration components
        self.tom_client = TomApiClient(tom_config.tom_api_url, tom_config.tom_timeout)
        self.tom_enabled = tom_config.enable_tom_integration
        self._last_processed_user_message_id: Optional[int] = None

        logger.info(f"TomCodeActAgent initialized with Tom integration: {self.tom_enabled}")
        if self.tom_enabled:
            logger.info(f"Tom API URL: {tom_config.tom_api_url}")

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
                # Create a new event loop for the async call
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_tom_instruction_sync, latest_user_message, formatted_messages, state)
                    tom_action = future.result(timeout=30)
            except Exception as e:
                logger.error(f"❌ Tom: Error in instruction improvement: {e}")
                tom_action = None
            if tom_action:
                logger.info(f"✅ Tom: Using Tom's suggestions to improve agent understanding")
                # Use Tom's suggestions to enhance the user message understanding
                enhanced_message = self._enhance_user_message_with_tom(tom_action, latest_user_message)
                # Update the formatted messages with the enhanced understanding
                formatted_messages = self._update_messages_with_enhanced_understanding(formatted_messages, enhanced_message)
                # Mark this message as processed
                self._last_processed_user_message_id = id(latest_user_message)
            else:
                logger.info(f"➡️ Tom: No improvement provided, continuing with original instruction")

        # Continue with normal CodeAct processing
        params: dict = {
            'messages': formatted_messages,
        }
        params['tools'] = check_tools(self.tools, self.llm.config)
        params['extra_body'] = {'metadata': state.to_llm_metadata(agent_name=self.name)}
        response = self.llm.completion(**params)
        logger.debug(f'Response from LLM: {response}')
        actions = self.response_to_actions(response)
        logger.debug(f'Actions after response_to_actions: {actions}')

        # INTEGRATION POINT 2: Suggest next actions when agent finishes
        finish_actions = [action for action in actions if isinstance(action, AgentFinishAction)]
        logger.debug(f"🔍 Tom: Integration Point 2 check - tom_enabled: {self.tom_enabled}, finish_actions: {len(finish_actions)}")

        if self.tom_enabled and finish_actions:
            logger.info(f"🚀 Tom: Integration Point 2 triggered - suggesting next actions")
            try:
                # Create a new event loop for the async call
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_tom_suggestions_sync, formatted_messages, state)
                    tom_suggestion = future.result(timeout=30)
            except Exception as e:
                logger.error(f"❌ Tom: Error in next action suggestions: {e}")
                tom_suggestion = None
            if tom_suggestion:
                # Use Tom's suggestions to enhance the finish action
                enhanced_finish = self._create_enhanced_finish_with_tom(tom_suggestion, actions)
                if enhanced_finish:
                    # Replace the original finish action with the enhanced one
                    finish_index = next(i for i, action in enumerate(actions)
                                      if isinstance(action, AgentFinishAction))
                    actions[finish_index] = enhanced_finish
                    logger.info(f"✅ Tom: Enhanced finish action with next action suggestions")
                else:
                    logger.info(f"➡️ Tom: Could not enhance finish action with Tom suggestions")
            else:
                logger.info(f"➡️ Tom: No next action suggestions provided")

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
        length_check = len(user_message.content.strip()) >= self.config.tom_min_instruction_length

        logger.debug(f"🔍 Tom: Message checks - source='{user_message.source}' (=='user': {source_check}), id={id(user_message)} (!=last: {id_check}), length={len(user_message.content.strip())} (>={self.config.tom_min_instruction_length}: {length_check})")

        return source_check and id_check and length_check

    def _run_tom_instruction_sync(self, user_message, formatted_messages, state):
        """Synchronous wrapper for async Tom instruction improvement."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._improve_instruction_with_tom(user_message, formatted_messages, state))
        finally:
            loop.close()

    def _run_tom_suggestions_sync(self, formatted_messages, state):
        """Synchronous wrapper for async Tom suggestions."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._suggest_next_actions_with_tom(formatted_messages, state))
        finally:
            loop.close()

    def _enhance_user_message_with_tom(self, tom_action: TomInstructionAction, user_message: MessageAction) -> str:
        """Enhance user message understanding using Tom's suggestions.

        Args:
            tom_action: The Tom action containing suggestions
            user_message: The original user message

        Returns:
            Enhanced instruction text based on Tom's suggestions
        """
        # Extract Tom's suggestions
        suggestions = tom_action.improved_instructions

        if not suggestions:
            logger.warning("🔄 Tom: No suggestions found in Tom action")
            return user_message.content

        # Get the best suggestion (first one, or highest confidence)
        best_suggestion = suggestions[0]
        if len(suggestions) > 1:
            # Find highest confidence suggestion
            best_suggestion = max(suggestions, key=lambda x: x.get('confidence_score', 0))

        improved_instruction = best_suggestion.get('improved_instruction', '')
        confidence = best_suggestion.get('confidence_score', 0)
        clarity = best_suggestion.get('clarity_score', 1.0)  # Default to 1.0 (clear) if not provided

        logger.info(f"🎯 Tom: Using suggestion - clarity: {clarity*100:.0f}%, confidence: {confidence*100:.0f}%")
        logger.info(f"💡 Tom: Improved instruction: {improved_instruction}")

        return improved_instruction

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

    def _create_enhanced_finish_with_tom(self, tom_suggestion: TomSuggestionAction, actions: list) -> Optional[AgentFinishAction]:
        """Create an enhanced finish action using Tom's next action suggestions.

        Args:
            tom_suggestion: The Tom suggestion action
            actions: List of actions including the original finish action

        Returns:
            Enhanced AgentFinishAction or None
        """
        # Find the original finish action
        original_finish = None
        for action in actions:
            if isinstance(action, AgentFinishAction):
                original_finish = action
                break

        if not original_finish:
            logger.warning("🔄 Tom: No finish action found to enhance")
            return None

        # Extract Tom's suggestions
        suggestions = tom_suggestion.suggestions

        if not suggestions:
            logger.warning("🔄 Tom: No suggestions found in Tom action")
            return None

        # Get the best suggestions (top 3)
        best_suggestions = suggestions[:3]

        # Create enhanced finish message
        original_content = getattr(original_finish, 'content', '') or getattr(original_finish, 'outputs', {}).get('content', '')

        enhanced_content = original_content
        if enhanced_content:
            enhanced_content += "\n\n"

        enhanced_content += "🎯 **What would you like to do next?**\n"

        for i, suggestion in enumerate(best_suggestions, 1):
            suggestion_text = suggestion.get('suggestion', '')
            reasoning = suggestion.get('reasoning', '')
            confidence = suggestion.get('confidence_score', 0)

            if suggestion_text:
                enhanced_content += f"\n{i}. {suggestion_text}"
                if reasoning:
                    enhanced_content += f" *(Why: {reasoning})*"

        enhanced_content += "\n\nFeel free to ask me to help with any of these or something else entirely!"

        logger.info(f"🎯 Tom: Enhanced finish action with {len(best_suggestions)} suggestions")

        # Create new finish action with enhanced content
        # AgentFinishAction uses final_thought for the main message content
        return AgentFinishAction(final_thought=enhanced_content)

    async def _improve_instruction_with_tom(
        self, user_message: MessageAction, formatted_messages: list, state: State
    ) -> Optional[TomInstructionAction]:
        """INTEGRATION POINT 1: Get instruction improvements from Tom.

        Args:
            user_message: The user message to improve
            formatted_messages: Full conversation context in LLM format
            state: Current agent state

        Returns:
            TomInstructionAction if improvements are available, None otherwise
        """
        try:
            user_id = self._get_user_id(state)
            context = self._extract_context_from_messages(formatted_messages)

            logger.info(f"🔄 Tom: Requesting instruction improvement for user: {user_id}")
            logger.info(f"📝 Tom: Original instruction: {user_message.content}")
            logger.info(f"📋 Tom: Context: {context}")

            # Call Tom API for instruction improvement
            response = await self.tom_client.propose_instructions(
                user_id=user_id,
                original_instruction=user_message.content,
                context=context
            )

            logger.info(f"✅ Tom: Received response: {response}")

            if response.get("success") and response.get("recommendations"):
                logger.info(f"🎯 Tom: Provided {len(response['recommendations'])} instruction improvements")
                for i, rec in enumerate(response['recommendations']):
                    logger.info(f"💡 Tom: Recommendation {i+1}: {rec}")

                return TomInstructionAction(
                    content="",  # Will be set in __post_init__
                    original_instruction=user_message.content,
                    improved_instructions=response["recommendations"]
                )
            else:
                logger.warning(f"⚠️ Tom: Instruction improvement failed: {response.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Tom: Instruction improvement failed with exception: {e}")
            if not self.config.tom_fallback_on_error:
                raise
            else:
                logger.warning(f"🔄 Tom: Falling back to original instruction due to error")

        return None

    async def _suggest_next_actions_with_tom(
        self, formatted_messages: list, state: State
    ) -> Optional[TomSuggestionAction]:
        """INTEGRATION POINT 2: Get next action suggestions from Tom.

        Args:
            formatted_messages: Full conversation context in LLM format
            state: Current agent state

        Returns:
            TomSuggestionAction if suggestions are available, None otherwise
        """
        try:
            user_id = self._get_user_id(state)
            context = self._extract_context_from_messages(formatted_messages)

            logger.info(f"🔄 Tom: Requesting next action suggestions for user: {user_id}")
            logger.info(f"📋 Tom: Context length: {len(context)} characters")

            # Call Tom API for next action suggestions
            response = await self.tom_client.suggest_next_actions(
                user_id=user_id,
                context=context
            )

            logger.info(f"✅ Tom: Received response: {response}")

            if response.get("success") and response.get("suggestions"):
                logger.info(f"🎯 Tom: Provided {len(response['suggestions'])} next action suggestions")
                for i, suggestion in enumerate(response['suggestions']):
                    logger.info(f"💡 Tom: Suggestion {i+1}: {suggestion}")

                return TomSuggestionAction(
                    content="",  # Will be set in __post_init__
                    suggestions=response["suggestions"],
                    context=context
                )
            else:
                logger.warning(f"⚠️ Tom: Next action suggestions failed: {response.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Tom: Next action suggestions failed with exception: {e}")
            if not self.config.tom_fallback_on_error:
                raise
            else:
                logger.warning(f"🔄 Tom: Continuing without next action suggestions due to error")

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

    def _get_user_id(self, state: State) -> str:
        """Get or generate user ID for Tom API calls.

        Args:
            state: Current agent state

        Returns:
            User ID string
        """
        # Use configured user ID if available
        if self.config.tom_user_id:
            return self.config.tom_user_id

        # Try to get from session or use default
        session_id = getattr(state, 'session_id', None) or 'default_user'
        return str(session_id)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup Tom client."""
        await self.tom_client.close()
