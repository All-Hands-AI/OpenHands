"""GitHub callback processor for V1 conversations."""

import asyncio
import logging
from uuid import UUID

from openhands.app_server.event_callback.event_callback_models import (
    EventCallback,
    EventCallbackProcessor,
    EventCallbackStatus,
)
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from openhands.app_server.services.injector import InjectorState
from openhands.app_server.user.specifiy_user_context import USER_CONTEXT_ATTR
from openhands.core.schema.agent import AgentState
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.sdk import Event, MessageEvent

_logger = logging.getLogger(__name__)


class GithubV1CallbackProcessor(EventCallbackProcessor):
    """
    V1 callback processor for sending conversation summaries to GitHub.

    This processor is used to send summaries of conversations to GitHub issues/PRs
    when agent state changes occur in V1 conversations.
    """

    github_view_data: dict  # Store serializable data instead of the view object
    send_summary_instruction: bool = True

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        """
        Process a conversation event by sending a summary to GitHub.

        Args:
            conversation_id: The conversation ID
            callback: The event callback
            event: The event that triggered the callback

        Returns:
            EventCallbackResult or None if the event should be ignored
        """
        # Only process AgentStateChangedObservation events
        if not isinstance(event, AgentStateChangedObservation):
            return None

        _logger.info(f'[GitHub V1] Callback agent state was {event.agent_state}')
        
        # Only process specific agent states
        if event.agent_state not in (
            AgentState.AWAITING_USER_INPUT,
            AgentState.FINISHED,
        ):
            return None

        try:
            from openhands.app_server.config import (
                get_app_conversation_service,
                get_event_callback_service,
                get_event_service,
                get_httpx_client,
            )

            # Create injector state with GitHub user context
            state = InjectorState()
            
            # Import here to avoid circular imports
            from integrations.github.github_view import GithubUserContext
            github_user_context = GithubUserContext(
                keycloak_user_id=self.github_view_data['keycloak_user_id'],
                git_provider_tokens=self.github_view_data.get('git_provider_tokens', {})
            )
            setattr(state, USER_CONTEXT_ATTR, github_user_context)

            async with (
                get_event_callback_service(state) as event_callback_service,
                get_app_conversation_service(state) as app_conversation_service,
                get_event_service(state) as event_service,
                get_httpx_client(state) as httpx_client,
            ):
                # If we need to send a summary instruction first
                if self.send_summary_instruction:
                    _logger.info(
                        f'[GitHub V1] Sending summary instruction for conversation {conversation_id}'
                    )

                    # Get the summary instruction
                    from integrations.utils import get_summary_instruction
                    summary_instruction = get_summary_instruction()

                    # Create a message event for the summary instruction
                    message_event = MessageEvent(
                        role="user",
                        content=[{"type": "text", "text": summary_instruction}]
                    )

                    # Save the event to the conversation
                    await event_service.save_event(conversation_id, message_event)

                    # Update the processor state
                    self.send_summary_instruction = False
                    callback.processor = self
                    callback.status = EventCallbackStatus.ACTIVE  # Keep active for next event
                    await event_callback_service.save_event_callback(callback)

                    _logger.info(
                        f'[GitHub V1] Sent summary instruction to conversation {conversation_id}'
                    )

                    return EventCallbackResult(
                        status=EventCallbackResultStatus.SUCCESS,
                        event_callback_id=callback.id,
                        event_id=event.id,
                        conversation_id=conversation_id,
                        detail="Summary instruction sent"
                    )

                # Extract the summary from the V1 conversation events
                _logger.info(
                    f'[GitHub V1] Extracting summary for conversation {conversation_id}'
                )

                # Get the app conversation to access the conversation URL
                app_conversation = await app_conversation_service.get_app_conversation(
                    conversation_id
                )
                if app_conversation is None:
                    raise RuntimeError(f"App conversation {conversation_id} not found")

                # Try to extract summary from conversation events
                summary = await self._extract_summary_from_v1_conversation(
                    httpx_client, app_conversation, conversation_id
                )

                # Add conversation footer
                from integrations.utils import append_conversation_footer
                summary_with_footer = append_conversation_footer(summary, str(conversation_id))

                # Send the summary to GitHub
                asyncio.create_task(self._send_message_to_github(summary_with_footer))

                _logger.info(f'[GitHub V1] Summary sent for conversation {conversation_id}')

                # Mark callback as completed
                callback.status = EventCallbackStatus.COMPLETED
                await event_callback_service.save_event_callback(callback)

                return EventCallbackResult(
                    status=EventCallbackResultStatus.SUCCESS,
                    event_callback_id=callback.id,
                    event_id=event.id,
                    conversation_id=conversation_id,
                    detail="Summary sent to GitHub"
                )

        except Exception as e:
            _logger.exception(
                f'[GitHub V1] Error processing conversation callback: {str(e)}'
            )
            
            # Mark callback as error
            try:
                from openhands.app_server.config import get_event_callback_service
                state = InjectorState()
                async with get_event_callback_service(state) as event_callback_service:
                    callback.status = EventCallbackStatus.ERROR
                    await event_callback_service.save_event_callback(callback)
            except Exception:
                _logger.exception("Failed to update callback status to ERROR")

            return EventCallbackResult(
                status=EventCallbackResultStatus.ERROR,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                detail=str(e)
            )

    async def _extract_summary_from_v1_conversation(
        self, httpx_client, app_conversation, conversation_id: UUID
    ) -> str:
        """
        Extract summary from V1 conversation events.
        
        This method attempts to find the agent's response to the summary instruction
        by looking through the conversation events.
        """
        try:
            # Try to get conversation events from the conversation URL
            # This might be available through different endpoints
            possible_endpoints = [
                f'{app_conversation.conversation_url}/events',
                f'{app_conversation.conversation_url}/messages',
                f'{app_conversation.conversation_url}/history'
            ]
            
            for endpoint in possible_endpoints:
                try:
                    response = await httpx_client.get(
                        endpoint,
                        headers={
                            'X-Session-API-Key': app_conversation.session_api_key,
                        },
                    )
                    
                    if response.status_code == 200:
                        events_data = response.json()
                        _logger.info(f'[GitHub V1] Got events from {endpoint}')
                        
                        # Look for agent messages that might contain the summary
                        summary = self._find_summary_in_events(events_data)
                        if summary:
                            return summary
                            
                except Exception as e:
                    _logger.debug(f'[GitHub V1] Endpoint {endpoint} failed: {e}')
                    continue
            
            # If we can't get events, return a fallback message
            _logger.warning(f'[GitHub V1] Could not extract summary from conversation {conversation_id}')
            return f'OpenHands conversation completed. [View full conversation](https://app.openhands.ai/conversations/{conversation_id}) for details.'
            
        except Exception as e:
            _logger.exception(f'[GitHub V1] Error extracting summary: {e}')
            return f'OpenHands conversation completed with errors. [View full conversation](https://app.openhands.ai/conversations/{conversation_id}) for details.'

    def _find_summary_in_events(self, events_data) -> str | None:
        """
        Find summary content in conversation events.
        
        This looks for agent messages that appear to be summaries,
        typically after a summary instruction was sent.
        """
        try:
            # Handle different possible event data structures
            events = []
            if isinstance(events_data, list):
                events = events_data
            elif isinstance(events_data, dict):
                events = events_data.get('events', events_data.get('messages', []))
            
            # Look for agent messages that might be summaries
            # This is a heuristic approach since we don't have the exact V0 event structure
            for event in reversed(events):  # Start from most recent
                if isinstance(event, dict):
                    # Look for agent/assistant messages
                    role = event.get('role', event.get('source', ''))
                    content = event.get('content', event.get('message', ''))
                    
                    if role in ['agent', 'assistant'] and content:
                        # If it's a substantial message (likely a summary), return it
                        if len(content) > 50:  # Arbitrary threshold
                            return content
            
            return None
            
        except Exception as e:
            _logger.exception(f'[GitHub V1] Error finding summary in events: {e}')
            return None

    async def _send_message_to_github(self, message: str) -> None:
        """
        Send a message to GitHub.

        Args:
            message: The message content to send to GitHub
        """
        try:
            # Import here to avoid circular imports
            from integrations.github.data_collector import GitHubDataCollector
            from integrations.github.github_manager import GithubManager
            from integrations.models import Message, SourceType
            from server.auth.token_manager import TokenManager

            # Create a message object for GitHub
            message_obj = Message(source=SourceType.OPENHANDS, message=message)

            # Get the token manager
            token_manager = TokenManager()

            # Create GitHub manager
            github_manager = GithubManager(token_manager, GitHubDataCollector())

            # Reconstruct the github_view from stored data
            # This is a simplified approach - in a real implementation you might want
            # to store more complete view data or reconstruct it differently
            from integrations.github.github_view import GithubIssue
            from integrations.types import UserData
            
            user_data = UserData(
                username=self.github_view_data['username'],
                user_id=self.github_view_data['user_id'],
                keycloak_user_id=self.github_view_data['keycloak_user_id']
            )

            # Create a minimal github_view for sending the message
            github_view = GithubIssue(
                issue_number=self.github_view_data['issue_number'],
                installation_id=self.github_view_data['installation_id'],
                full_repo_name=self.github_view_data['full_repo_name'],
                is_public_repo=self.github_view_data['is_public_repo'],
                user_info=user_data,
                raw_payload=None,  # Not needed for sending messages
                conversation_id=self.github_view_data['conversation_id'],
                uuid=self.github_view_data.get('uuid'),
                should_extract=False,
                send_summary_instruction=False,
                title=self.github_view_data.get('title', ''),
                description=self.github_view_data.get('description', ''),
                previous_comments=[]
            )

            # Send the message
            await github_manager.send_message(message_obj, github_view)

            _logger.info(
                f'[GitHub V1] Sent summary message to {github_view.full_repo_name}#{github_view.issue_number}'
            )
        except Exception as e:
            _logger.exception(f'[GitHub V1] Failed to send summary message: {str(e)}')