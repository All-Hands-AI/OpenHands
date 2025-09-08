"""TomCodeActAgent: CodeAct Agent enhanced with Tom agent integration."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from openhands.events.action import Action

from litellm import ChatCompletionToolParam
from tom_swe.memory.locations import (  # type: ignore
    get_overall_user_model_filename,
    get_usermodeling_dir,
)
from tom_swe.tom_agent import create_tom_agent  # type: ignore

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.tools.tom_consult_agent import (
    ConsultTomAgentTool,
)
from openhands.cli.tui import (
    CLI_DISPLAY_LEVEL,
    capture_tom_thinking,
    display_instruction_improvement,
)
from openhands.controller.state.state import State
from openhands.controller.state.state_tracker import StateTracker
from openhands.core.config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import TextContent
from openhands.events.action import (
    AgentFinishAction,
    ConsultTomAgentAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.memory.condenser.condenser import Condensation, View
from openhands.memory.conversation_memory import ConversationMemory
from openhands.server.services.conversation_stats import ConversationStats
from openhands.storage import get_file_store
from openhands.storage.locations import CONVERSATION_BASE_DIR
from openhands.utils.analytics import track_tom_event
from openhands.utils.prompt import PromptManager

CLI_AVAILABLE = os.environ.get('CLI_AVAILABLE', 'True').lower() == 'true'


class TomCodeActAgent(CodeActAgent):
    """CodeAct Agent enhanced with Tom agent integration.

    This agent extends CodeActAgent to provide personalized guidance through
    the Tom agent at two key integration points:
    1. When a user message is received - improve the instruction
    2. When the agent finishes a task - suggest next actions
    """

    VERSION = '1.0'

    def __init__(self, config: AgentConfig, llm_registry: LLMRegistry) -> None:
        """Initialize TomCodeActAgent.

        Args:
            llm: Language model to use
            config: Agent configuration with Tom settings
        """
        super().__init__(config, llm_registry)
        self.file_store = get_file_store(
            'local', '~/.openhands'
        )  # temporary way to get file store

        # Store Tom configuration parameters from config
        self.tom_enabled = config.enable_tom_integration
        self.tom_enable_rag = config.tom_enable_rag
        self.tom_min_instruction_length = config.tom_min_instruction_length
        self.skip_memory_collection = config.skip_memory_collection
        # Tom integration components
        self.tom_agent = create_tom_agent(
            file_store=self.file_store,
            enable_rag=config.tom_enable_rag,
            llm_model=self.llm.config.model,
            api_key=self.llm.config.api_key.get_secret_value()
            if self.llm.config.api_key
            else None,
            api_base=self.llm.config.base_url,
            skip_memory_collection=config.skip_memory_collection,
        )
        self._last_processed_user_message_id: Optional[int] = None
        self._skip_next_tom_analysis: bool = False
        self._initialization_tracked: bool = False

        logger.info(
            f'TomCodeActAgent initialized with Tom integration: {self.tom_enabled}'
        )

    def _get_tools(self) -> list['ChatCompletionToolParam']:
        """Override to add Tom consult agent tool."""
        tools = super()._get_tools()
        tools.append(ConsultTomAgentTool)
        return tools

    def step(self, state: State) -> 'Action':
        """Enhanced step method with Tom integration."""
        # Track ToM agent initialization on first step (CLI mode only)
        if not self._initialization_tracked and CLI_AVAILABLE:
            try:
                track_tom_event(
                    event='tom_agent_initialized',
                    properties={
                        'session_id': state.session_id,
                        'tom_enabled': self.tom_enabled,
                        'tom_enable_rag': self.tom_enable_rag,
                        'tom_min_instruction_length': self.tom_min_instruction_length,
                        'skip_memory_collection': self.skip_memory_collection,
                        'llm_model': self.llm.config.model,
                    },
                )
                self._initialization_tracked = True
            except Exception as e:
                logger.error(f'Failed to track ToM agent initialization: {e}')

        action: 'Action | None' = None
        latest_user_message = state.get_last_user_message()
        # sleep time compute at the beginning of the session

        if latest_user_message:
            if latest_user_message.content.strip() == '/sleeptime':
                self.sleeptime_compute(user_id=state.user_id or '')
                return AgentFinishAction()
            elif (
                latest_user_message.content.strip() == '/tom_give_suggestions'
                and self._is_new_user_message(latest_user_message)
            ):
                action = ConsultTomAgentAction(
                    content='Users message is /tom_give_suggestions. I better consult ToM agent about what user wants to do next and get some user preferences.',
                    use_user_message=False,
                    custom_query='what user wants to do next',
                )
                self._last_processed_user_message_id = latest_user_message.id

        if action is None:
            action = super().step(state)
        if isinstance(action, ConsultTomAgentAction):
            logger.info(
                '🔧 Tom: Detected ConsultTomAgentAction, triggering Tom consultation'
            )
            # Format messages for Tom processing
            condensed_history: list[Event] = []
            match self.condenser.condensed_history(state):
                case View(events=events):
                    condensed_history = events
                case Condensation(action=condensation_action):
                    return condensation_action

            initial_user_message = self._get_initial_user_message(state.history)
            messages = self._get_messages(condensed_history, initial_user_message)
            formatted_messages = self.llm.format_messages_for_llm(messages)[1:]

            # Determine what to consult about
            if self._has_tom_consultation_happened(formatted_messages):
                consultation_result: Optional[str] = (
                    'Tom agent has already given suggestions for the SWE agent. No need to consult Tom agent again.'
                )

            elif action.use_user_message and latest_user_message:
                consultation_result = self.tom_consult_agent(
                    query_text=f"I am SWE agent. {action.content}. I need to consult ToM agent about the user's message: {latest_user_message.content}",
                    formatted_messages=formatted_messages,
                    state=state,
                    is_user_query=True,
                )
            elif action.custom_query:
                consultation_result = self.tom_consult_agent(
                    query_text=f'I am SWE agent. {action.content}. I need to consult ToM agent: {action.custom_query}',
                    formatted_messages=formatted_messages,
                    state=state,
                    is_user_query=False,
                )
            else:
                logger.warning('⚠️ Tom: No query specified for consultation')
                consultation_result = None

            # Return action to update the observation with the consultation result
            if consultation_result:
                logger.info(
                    '✅ Tom: Requesting observation update with consultation result'
                )
                query_description = action.custom_query or "the user's message"
                return ConsultTomAgentAction(
                    content=action.content
                    + f'I need to consult Tom agent about {query_description}'
                    + '\n\n[Starting consultation with Tom agent...]'
                    + consultation_result
                    + '\n\n[Finished consulting with ToM Agent...]',
                    use_user_message=action.use_user_message,
                    custom_query=action.custom_query,
                )
            else:
                logger.warning('⚠️ Tom: No consultation result received')

        # If finishing and Tom enabled, run sleeptime compute
        if (
            isinstance(action, AgentFinishAction)
            and self.tom_enabled
            and not self.skip_memory_collection
        ):
            logger.info('🚀 Tom: Running sleeptime compute on finish')
            self.sleeptime_compute(user_id=state.user_id or '')

        return action

    def _is_new_user_message(self, user_message: MessageAction) -> bool:
        """Check if this is a new user message that should be processed with Tom.

        Args:
            user_message: The user message to check

        Returns:
            True if this is a new user message that should trigger Tom improvement
        """
        source_check = user_message.source == 'user'
        id_check = user_message.id != self._last_processed_user_message_id
        length_check = (
            len(user_message.content.strip()) >= self.tom_min_instruction_length
        )

        return source_check and id_check and length_check

    def _has_tom_consultation_happened(self, formatted_messages: list) -> bool:
        """Check if Tom agent has already completed its consultation.

        Args:
            formatted_messages: The formatted message history

        Returns:
            True if Tom agent consultation is complete (marked with Done_communicating_with_Tom_agent)
        """
        if not formatted_messages:
            return False

        # Check the last two messages for the completion marker
        messages_to_check = (
            formatted_messages[-2:]
            if len(formatted_messages) >= 2
            else formatted_messages[-1:]
        )

        for message in messages_to_check:
            try:
                # Safely check if message has content and text
                if (
                    isinstance(message, dict)
                    and 'content' in message
                    and isinstance(message['content'], list)
                    and len(message['content']) > 0
                    and isinstance(message['content'][0], dict)
                    and 'text' in message['content'][0]
                ):
                    text_content = message['content'][0]['text']
                    if (
                        text_content
                        and '</Done_communicating_with_Tom_agent>' in text_content
                    ):
                        return True
            except (KeyError, IndexError, TypeError):
                # If we can't access the text content, continue to next message
                continue

        return False

    def tom_consult_agent(
        self,
        query_text: str,
        formatted_messages: list,
        state: State,
        is_user_query: bool = True,
    ) -> Optional[str]:
        """INTEGRATION POINT 1: Get guidance from Tom agent.

        Args:
            query_text: The text to query Tom agent about
            formatted_messages: Full conversation context in LLM format
            state: Current agent state
            is_user_query: Whether this is about a user message or agent query

        Returns:
            Tom agent's guidance if available, None otherwise
        """

        try:
            user_id = state.user_id or ''
            # Single synchronous call that includes user context analysis
            # Capture tom thinking process in CLI if available
            if CLI_AVAILABLE:
                with capture_tom_thinking():
                    logger.log(
                        CLI_DISPLAY_LEVEL,
                        '🚀 Tom: Theory of minding...',
                    )
                    tom_suggestion = self.tom_agent.give_suggestions(
                        user_id=user_id,
                        query=query_text,
                        formatted_messages=formatted_messages,
                    )
            else:
                tom_suggestion = self.tom_agent.give_suggestions(
                    user_id=user_id,
                    query=query_text,
                    formatted_messages=formatted_messages,
                )
            if tom_suggestion:
                logger.debug('✅ Tom: Received consultation result')
                logger.debug(f'💡 Tom: Consultation result: {tom_suggestion}')
                # In CLI mode, show consultation result to user and get their choice
                if CLI_AVAILABLE:
                    user_response = display_instruction_improvement(
                        original_instruction=query_text,
                        suggestions=tom_suggestion.suggestions,
                    )

                    # Record the interaction with tri-state value
                    try:
                        user_data_dir = Path(get_usermodeling_dir(user_id))
                        record_file = user_data_dir / 'interaction_record.jsonl'

                        interaction = {
                            'session_id': state.session_id,
                            'original': query_text,
                            'improved': tom_suggestion.suggestions,
                            'accepted': user_response['value'],  # Now 1, 0.5, or 0
                            'timestamp': datetime.now().isoformat(),
                            'is_user_query': is_user_query,
                        }
                        track_tom_event(
                            event='tom_consult_agent_interaction',
                            properties=interaction,
                        )

                        # Append to JSONL file (read existing content + append new line)
                        new_line = json.dumps(interaction) + '\n'
                        if self.file_store.exists(str(record_file)):  # type: ignore
                            existing_content = self.file_store.read(str(record_file))
                            self.file_store.write(
                                str(record_file), existing_content + new_line
                            )
                        else:
                            self.file_store.write(str(record_file), new_line)
                        logger.log(CLI_DISPLAY_LEVEL, '🔍 Tom: Recorded interaction')

                        return user_response['suggestions']

                    except Exception as e:
                        logger.error(f'❌ Tom: Failed to record interaction: {e}')
                        return user_response['suggestions']
                else:
                    # Non-CLI mode: use consultation result automatically
                    logger.info("✅ Tom: Using Tom's guidance")

                    return tom_suggestion.suggestions
            else:
                logger.warning(
                    '⚠️ Tom: No guidance provided (could be the query is clear enough)'
                )

        except Exception as e:
            logger.error(f'❌ Tom: Error in consultation: {e}')
        return None

    def sleeptime_compute(
        self,
        user_id: str = '',
    ) -> None:
        """Fetch unprocessed sessions data and send to tom-swe sleeptime compute.

        This function pulls all unprocessed sessions data and processes them
        with the tom-swe sleeptime_compute functionality.

        Args:
            user_id: User ID for Tom-swe processing
        """
        logger.info('🔄 Tom: Starting sleeptime compute process')

        # Track sleeptime compute trigger
        try:
            if self.file_store.exists(get_overall_user_model_filename(user_id)):  # type: ignore
                overall_user_model_content = self.file_store.read(
                    get_overall_user_model_filename(user_id)
                )
                overall_user_model: dict[str, Any] = json.loads(
                    overall_user_model_content
                )
            else:
                overall_user_model = {'user_profile': 'unknown'}
            track_tom_event(
                event='tom_sleeptime_triggered',
                properties=overall_user_model,
            )
        except Exception as e:
            logger.error(f'Failed to track sleeptime compute trigger: {e}')

        # Get all available sessions
        try:
            session_paths = self.file_store.list(CONVERSATION_BASE_DIR)
            all_sessions = [
                Path(path).name
                for path in session_paths
                if not Path(path).name.startswith('.')
            ]
        except FileNotFoundError:
            logger.info('📭 Tom: No sessions directory found')
            return

        # Load processing history
        processing_history = self.load_processing_history(user_id)

        # Check which sessions need processing
        sessions_to_process: list[dict[str, str | int]] = []
        for session_id in all_sessions:
            should_process, current_event_id = self.should_reprocess_session(
                session_id, processing_history
            )
            if should_process:
                sessions_to_process.append(
                    {'session_id': session_id, 'current_event_id': current_event_id}
                )
                logger.info(
                    f'📋 Tom: Session {session_id} needs processing (events up to {current_event_id})'
                )

        if not sessions_to_process:
            logger.info('📭 Tom: No sessions need processing')
            return

        logger.info(f'📊 Tom: Found {len(sessions_to_process)} sessions to process')

        # Collect session data using existing logic from sleeptime.py
        session_ids_to_process = [str(s['session_id']) for s in sessions_to_process]
        sessions_data = self._get_sessions_data(session_ids_to_process, self.file_store)
        # limite to 30 latest sessions (end_time)
        sessions_data_limited = sorted(
            sessions_data, key=lambda x: x['end_time'], reverse=True
        )[:30]

        # TEMPORARY: copy sessions to user's modeling dir under raw_sessions dir
        raw_sessions_dir = (
            Path(self.file_store.get_full_path(get_usermodeling_dir(user_id)))  # type: ignore
            / 'raw_sessions'
        )
        raw_sessions_dir.mkdir(parents=True, exist_ok=True)

        for session_id in [session['session_id'] for session in sessions_data_limited]:
            dest_path = raw_sessions_dir / session_id
            # Remove existing directory if it exists to force overwrite
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(
                Path(self.file_store.get_full_path(CONVERSATION_BASE_DIR)) / session_id,  # type: ignore
                dest_path,
            )

        if not sessions_data_limited:
            logger.info('📭 Tom: No valid session data extracted')
            return

        logger.info(
            f'📊 Tom: Successfully extracted {len(sessions_data_limited)} sessions'
        )

        # Call tom_agent.sleeptime_compute in a thread pool to avoid event loop conflict
        import concurrent.futures

        def run_sleeptime_compute():
            if CLI_AVAILABLE:
                with capture_tom_thinking():
                    self.tom_agent.sleeptime_compute(
                        sessions_data=sessions_data_limited, user_id=user_id
                    )
            else:
                self.tom_agent.sleeptime_compute(
                    sessions_data=sessions_data_limited, user_id=user_id
                )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_sleeptime_compute)
            try:
                future.result()  # Wait for completion and get any exception

                # Only update processing history on success
                current_timestamp = datetime.now().isoformat()
                for session_info in sessions_to_process:
                    processing_history[str(session_info['session_id'])] = {
                        'processed_at': current_timestamp,
                        'last_event_id': session_info['current_event_id'],
                    }

                self.save_processing_history(user_id, processing_history)
                logger.info(
                    f'📝 Tom: Updated processing history for {len(sessions_to_process)} sessions'
                )
                logger.info('✅ Tom: Sleeptime compute completed successfully')

            except Exception as e:
                logger.error(f'❌ Tom: Sleeptime compute failed: {e}')
                logger.info('⚠️ Tom: Processing history not updated due to failure')
                return

    def get_session_last_event_id(self, session_id: str) -> int:
        """Get the highest numbered event file in a session's events directory."""
        events_dir = f'{CONVERSATION_BASE_DIR}/{session_id}/events'
        if not self.file_store.exists(events_dir):  # type: ignore
            return -1

        event_files = self.file_store.list(events_dir)
        event_numbers = []
        for file_path in event_files:
            filename = Path(file_path).name
            if filename.endswith('.json'):
                try:
                    event_numbers.append(int(filename[:-5]))  # Remove .json
                except ValueError:
                    continue

        return max(event_numbers) if event_numbers else -1

    def load_processing_history(self, user_id: str) -> dict:
        """Load processing history from JSON file."""
        history_file = (
            f'{get_usermodeling_dir(user_id)}/processed_sessions_timestamps.json'
        )
        if self.file_store.exists(history_file):  # type: ignore
            try:
                content = self.file_store.read(history_file)
                return json.loads(content)
            except Exception as e:
                logger.error(f'❌ Tom: Failed to load processing history: {e}')
                return {}
        return {}

    def save_processing_history(self, user_id: str, history: dict):
        """Save processing history to JSON file."""
        history_file = (
            f'{get_usermodeling_dir(user_id)}/processed_sessions_timestamps.json'
        )
        self.file_store.write(history_file, json.dumps(history, indent=2))

    def should_reprocess_session(
        self, session_id: str, history: dict
    ) -> tuple[bool, int]:
        """Check if session should be reprocessed. Returns (should_process, current_event_id)."""
        current_event_id = self.get_session_last_event_id(session_id)

        if current_event_id == -1:  # No events directory
            return False, -1

        if session_id not in history:  # Never processed
            return True, current_event_id

        stored_event_id = history[session_id].get('last_event_id', -1)
        return current_event_id > stored_event_id, current_event_id

    def _get_sessions_data(
        self, session_ids: list[str], file_store: Any
    ) -> list[dict[str, Any]]:
        """Extract sessions data using OpenHands infrastructure."""

        # Create ConversationMemory components (minimal setup)
        agent_config = AgentConfig()
        # Use CodeActAgent prompts instead of TomCodeActAgent-specific prompts
        prompt_dir = os.path.join(
            os.path.dirname(__file__), '..', 'codeact_agent', 'prompts'
        )
        prompt_manager = PromptManager(prompt_dir=prompt_dir)
        conversation_memory = ConversationMemory(agent_config, prompt_manager)

        sessions_data = []

        for session_id in session_ids:
            try:
                event_stream = EventStream(
                    sid=session_id, file_store=file_store, user_id=None
                )

                # Use StateTracker to get properly filtered history
                state_tracker = StateTracker(session_id, file_store, None)
                state_tracker.set_initial_state(
                    id=session_id,
                    conversation_stats=ConversationStats(
                        file_store=file_store, conversation_id=session_id, user_id=None
                    ),
                    state=None,
                    max_iterations=100,
                    max_budget_per_task=None,
                    confirmation_mode=False,
                )
                state_tracker._init_history(event_stream)
                events = state_tracker.state.history

                if not events:
                    logger.warning(f'⚠️ Tom: No events found in session {session_id}')
                    continue

                logger.debug(
                    f'📝 Tom: Processing session {session_id}: {len(events)} events'
                )

                # Find the initial user message
                initial_user_action = None
                for event in events:
                    if isinstance(event, MessageAction) and event.source == 'user':
                        initial_user_action = event
                        break

                if not initial_user_action:
                    logger.warning(
                        f'⚠️ Tom: No initial user message found for session {session_id}'
                    )
                    continue
                # Process events into conversation format
                messages = conversation_memory.process_events(
                    condensed_history=events,
                    initial_user_action=initial_user_action,
                    vision_is_active=False,
                )

                # Convert messages to tom-swe format
                conversation_messages = self._messages_to_conversation_text(messages)
                logger.debug(
                    f'✅ Tom: Converted session {session_id} to conversation ({len(conversation_messages)} messages)'
                )

                # Collect session data in tom-swe expected format
                session_data = {
                    'session_id': session_id,
                    'start_time': events[0].timestamp,
                    'end_time': events[-1].timestamp,
                    'event_count': len(events),
                    'message_count': len(messages),
                    'conversation_messages': conversation_messages,
                }
                sessions_data.append(session_data)

            except Exception as e:
                logger.error(f'❌ Tom: Failed to process session {session_id}: {e}')
                continue

        return sessions_data

    def _messages_to_conversation_text(self, messages) -> list[dict[str, str]]:
        """Convert ConversationMemory messages to tom-swe format."""
        conversation_messages = []

        for message in messages:
            text_parts = []
            for content in message.content:
                if isinstance(content, TextContent):
                    text_parts.append(content.text)

            if text_parts:
                content_text = '\n'.join(text_parts)
                conversation_messages.append(
                    {'role': message.role, 'content': content_text}
                )

        return conversation_messages
