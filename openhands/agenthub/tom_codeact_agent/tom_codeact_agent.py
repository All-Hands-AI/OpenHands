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
    
    def __init__(self, llm: LLM, config: TomCodeActAgentConfig) -> None:
        """Initialize TomCodeActAgent.
        
        Args:
            llm: Language model to use
            config: Agent configuration including Tom settings
        """
        super().__init__(llm, config)
        
        # Tom integration components
        self.tom_client = TomApiClient(config.tom_api_url, config.tom_timeout)
        self.tom_enabled = config.enable_tom_integration
        self._last_processed_user_message_id: Optional[int] = None
        
        logger.info(f"TomCodeActAgent initialized with Tom integration: {self.tom_enabled}")
        if self.tom_enabled:
            logger.info(f"Tom API URL: {config.tom_api_url}")
    
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
            
            tom_action = asyncio.run(self._improve_instruction_with_tom(
                latest_user_message, formatted_messages, state
            ))
            if tom_action:
                return tom_action
        
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
        if self.tom_enabled and finish_actions:
            tom_suggestion = asyncio.run(self._suggest_next_actions_with_tom(
                formatted_messages, state
            ))
            if tom_suggestion:
                # Insert Tom suggestion before the finish action
                finish_index = next(i for i, action in enumerate(actions) 
                                  if isinstance(action, AgentFinishAction))
                actions.insert(finish_index, tom_suggestion)
        
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
        return (
            user_message.source == 'user' and
            id(user_message) != self._last_processed_user_message_id and
            len(user_message.content.strip()) >= self.config.tom_min_instruction_length
        )
    
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
            
            logger.info(f"Requesting instruction improvement from Tom for user: {user_id}")
            
            # Call Tom API for instruction improvement
            response = await self.tom_client.propose_instructions(
                user_id=user_id,
                original_instruction=user_message.content,
                context=context
            )
            
            if response.get("success") and response.get("recommendations"):
                # Mark this message as processed to avoid duplicate processing
                self._last_processed_user_message_id = id(user_message)
                
                logger.info(f"Tom provided {len(response['recommendations'])} instruction improvements")
                
                return TomInstructionAction(
                    original_instruction=user_message.content,
                    improved_instructions=response["recommendations"]
                )
            else:
                logger.warning(f"Tom instruction improvement failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Tom instruction improvement failed with exception: {e}")
            if not self.config.tom_fallback_on_error:
                raise
        
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
            
            logger.info(f"Requesting next action suggestions from Tom for user: {user_id}")
            
            # Call Tom API for next action suggestions
            response = await self.tom_client.suggest_next_actions(
                user_id=user_id,
                context=context
            )
            
            if response.get("success") and response.get("suggestions"):
                logger.info(f"Tom provided {len(response['suggestions'])} next action suggestions")
                
                return TomSuggestionAction(
                    suggestions=response["suggestions"],
                    context=context
                )
            else:
                logger.warning(f"Tom next action suggestions failed: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Tom next action suggestions failed with exception: {e}")
            if not self.config.tom_fallback_on_error:
                raise
        
        return None
    
    def _extract_context_from_messages(self, formatted_messages: list) -> str:
        """Extract context from the formatted LLM messages.
        
        Args:
            formatted_messages: Messages formatted for LLM consumption
            
        Returns:
            String representation of the conversation context
        """
        context_parts = []
        
        for message in formatted_messages[-10:]:  # Last 10 messages for context
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