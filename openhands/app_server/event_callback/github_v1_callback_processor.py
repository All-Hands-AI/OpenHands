import logging
import os
from uuid import UUID

import httpx
from github import Github, GithubIntegration
from pydantic import Field

from openhands.agent_server.models import SendMessageRequest
from openhands.app_server.event_callback.event_callback_models import (
    EventCallback,
    EventCallbackProcessor,
)
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from openhands.app_server.sandbox.sandbox_models import AGENT_SERVER, SandboxStatus
from openhands.app_server.utils.docker_utils import (
    replace_localhost_hostname_for_docker,
)
from openhands.sdk import Event, TextContent, conversation
from openhands.sdk.event import ConversationStateUpdateEvent
from openhands.agent_server.models import EventPage

_logger = logging.getLogger(__name__)


class GithubV1CallbackProcessor(EventCallbackProcessor):
    """Callback processor for GitHub V1 integrations."""

    github_view_data: dict = Field(default_factory=dict)
    send_summary_instruction: bool = Field(default=True)
    should_extract: bool = Field(default=True)

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult | None:
        """Process events for GitHub V1 integration."""
        if not isinstance(event, ConversationStateUpdateEvent):
            return None

        if event.key != 'execution_status' and event.value != 'finished':
            return None

        _logger.info(f'[GitHub V1] Callback agent state was {event}')
        _logger.info(f'[GitHub V1] Is summary sent: {self.send_summary_instruction}')

        if self.send_summary_instruction:
            self.send_summary_instruction = False
            _logger.info(f'[GitHub V1] Sending summary instruction: {conversation_id}')
            return await self._send_summary_instruction(
                conversation_id,
                callback,
                event,
            )

        if self.should_extract:
            self.should_extract = False
            _logger.info(
                f'[GitHub V1] Extracting summary for conversation: {conversation_id}'
            )

            # Import services within the method to avoid circular imports
            from openhands.app_server.config import (
                get_app_conversation_info_service,
                get_httpx_client,
                get_sandbox_service,
            )
            from openhands.app_server.services.injector import InjectorState
            from openhands.app_server.user.specifiy_user_context import (
                ADMIN,
                USER_CONTEXT_ATTR,
            )

            from openhands.server.shared import conversation_manager

            # agent_loop_infos = await conversation_manager.get_agent_loop_info(
            #     filter_to_sids={conversation_id.}
            # )
            # event_store = agent_loop_infos[0].event_store
            # events: list = event_store.get_matching_events(
            #     limit=10,
            #     reverse=True,
            # )


            try:
                # Create injector state for dependency injection
                state = InjectorState()
                setattr(state, USER_CONTEXT_ATTR, ADMIN)

                async with (
                    get_app_conversation_info_service(
                        state
                    ) as app_conversation_info_service,
                    get_sandbox_service(state) as sandbox_service,
                    get_httpx_client(state) as httpx_client,
                ):
                    # Get conversation info to find the sandbox
                    app_conversation_info = (
                        await app_conversation_info_service.get_app_conversation_info(
                            conversation_id
                        )
                    )
                    if not app_conversation_info:
                        _logger.error(
                            f'[GitHub V1] Conversation not found for summary extraction: {conversation_id}'
                        )
                        return EventCallbackResult(
                            status=EventCallbackResultStatus.ERROR,
                            event_callback_id=callback.id,
                            event_id=event.id,
                            conversation_id=conversation_id,
                            detail='Conversation not found',
                        )

                    # Get sandbox info to find agent server URL
                    sandbox = await sandbox_service.get_sandbox(
                        app_conversation_info.sandbox_id
                    )
                    if not sandbox or sandbox.status != SandboxStatus.RUNNING:
                        _logger.error(
                            f'[GitHub V1] Sandbox not running for summary extraction: {app_conversation_info.sandbox_id}'
                        )
                        return EventCallbackResult(
                            status=EventCallbackResultStatus.ERROR,
                            event_callback_id=callback.id,
                            event_id=event.id,
                            conversation_id=conversation_id,
                            detail='Sandbox not running',
                        )

                    # Validate session API key
                    if not sandbox.session_api_key:
                        _logger.error(
                            f'[GitHub V1] No session API key for summary extraction: {sandbox.id}'
                        )
                        return EventCallbackResult(
                            status=EventCallbackResultStatus.ERROR,
                            event_callback_id=callback.id,
                            event_id=event.id,
                            conversation_id=conversation_id,
                            detail='No session API key available',
                        )

                    # Get agent server URL
                    agent_server_url = self._get_agent_server_url(sandbox)

                    # Extract summary from the latest agent message
                    summary = await self._extract_summary(
                        httpx_client=httpx_client,
                        agent_server_url=agent_server_url,
                        conversation_id=conversation_id,
                        session_api_key=sandbox.session_api_key,
                    )

                    if not summary:
                        _logger.warning(
                            f'[GitHub V1] No summary extracted for conversation: {conversation_id}'
                        )
                        return EventCallbackResult(
                            status=EventCallbackResultStatus.SUCCESS,
                            event_callback_id=callback.id,
                            event_id=event.id,
                            conversation_id=conversation_id,
                            detail='No summary found to post',
                        )

                    # Post summary to GitHub
                    await self._post_summary_to_github(summary)

                    return EventCallbackResult(
                        status=EventCallbackResultStatus.SUCCESS,
                        event_callback_id=callback.id,
                        event_id=event.id,
                        conversation_id=conversation_id,
                        detail='Summary posted to GitHub successfully',
                    )

            except Exception as e:
                _logger.exception(
                    f'[GitHub V1] Error extracting and posting summary: {e}'
                )
                return EventCallbackResult(
                    status=EventCallbackResultStatus.ERROR,
                    event_callback_id=callback.id,
                    event_id=event.id,
                    conversation_id=conversation_id,
                    detail=str(e),
                )

        # If neither condition is met, return None
        return None

    def _get_installation_access_token(
        self,
    ) -> str:
        installation_id = self.github_view_data.get('installation_id')

        if not installation_id:
            raise ValueError(
                f'Missing installation ID for Github Payload: {self.github_view_data}'
            )

        GITHUB_APP_CLIENT_ID = os.getenv('GITHUB_APP_CLIENT_ID', '').strip()
        GITHUB_APP_PRIVATE_KEY = os.getenv('GITHUB_APP_PRIVATE_KEY', '').replace(
            '\\n', '\n'
        )

        github_integration = GithubIntegration(
            GITHUB_APP_CLIENT_ID, GITHUB_APP_PRIVATE_KEY
        )
        token_data = github_integration.get_access_token(installation_id)
        return token_data.token

    async def _extract_summary(
        self,
        httpx_client: httpx.AsyncClient,
        agent_server_url: str,
        conversation_id: UUID,
        session_api_key: str,
    ) -> str:
        """Extract summary from the latest agent message in the conversation.

        Args:
            httpx_client: HTTP client for making API requests
            agent_server_url: URL of the agent server
            conversation_id: ID of the conversation
            session_api_key: API key for authentication

        Returns:
            str: The content of the last agent message, or empty string if none found
        """
        try:
            # Get the latest events from the conversation using the events search endpoint
            url = f'{agent_server_url.rstrip("/")}/api/conversations/{conversation_id.hex}/events/search'
            headers = {'X-Session-API-Key': session_api_key}
            params = {
                'limit': 10,
                'sort_order': 'TIMESTAMP_DESC',
            }

            _logger.debug(
                f'[GitHub V1] Fetching events from {url} with params: {params}'
            )

            response = await httpx_client.get(
                url,
                headers=headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()

            page = EventPage.model_validate(response.json())

            events = page.items
            for event in events:
                print('event fetched', event)


            # Look for the most recent agent message (reverse order since we want the latest)
            # agent_messages_found = 0
            # for event in reversed(events):
            #     # Check if this is an agent message action
            #     if event.get('source') == 'agent':
            #         agent_messages_found += 1
            #         _logger.debug(
            #             f'[GitHub V1] Found agent event: action={event.get("action")}, keys={list(event.keys())}'
            #         )

            #         if event.get('action') == 'message':
            #             # Try different possible content fields
            #             content = None
            #             if 'content' in event:
            #                 content = event['content']
            #             elif 'message' in event:
            #                 content = event['message']
            #             elif hasattr(event, 'content'):
            #                 content = getattr(event, 'content')

            #             if content:
            #                 _logger.info(
            #                     f'[GitHub V1] Found agent message: {content[:100]}...'
            #                 )
            #                 return content
            #             else:
            #                 _logger.debug(
            #                     f'[GitHub V1] Agent message event found but no content field: {event}'
            #                 )

            _logger.warning(
                f'[GitHub V1] No agent messages found in recent events (found {agent_messages_found} agent events total)'
            )

            # If no agent messages found, log a sample of events for debugging
            if events:
                _logger.debug(f'[GitHub V1] Sample event structure: {events[0]}')

            return ''

        except httpx.HTTPStatusError as e:
            error_detail = f'HTTP {e.response.status_code} error'
            try:
                error_body = e.response.text
                if error_body:
                    error_detail += f': {error_body}'
            except Exception:
                pass

            _logger.error(
                f'[GitHub V1] HTTP error fetching events from {url}: {error_detail}',
                exc_info=True,
            )
            return ''

        except httpx.TimeoutException:
            _logger.error(
                f'[GitHub V1] Timeout fetching events from {url}',
                exc_info=True,
            )
            return ''

        except httpx.RequestError as e:
            _logger.error(
                f'[GitHub V1] Request error fetching events from {url}: {str(e)}',
                exc_info=True,
            )
            return ''

        except Exception as e:
            _logger.error(
                f'[GitHub V1] Unexpected error extracting summary: {str(e)}',
                exc_info=True,
            )
            return ''

    async def _post_summary_to_github(self, summary: str):
        installation_token = self._get_installation_access_token()

        full_repo_name = self.github_view_data['full_repo_name']
        issue_number = self.github_view_data['issue_number']

        with Github(installation_token) as github_client:
            repo = github_client.get_repo(full_repo_name)
            issue = repo.get_issue(number=issue_number)
            issue.create_comment(summary)

    async def _send_summary_instruction(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ):
        # Import services within the method to avoid circular imports
        from openhands.app_server.config import (
            get_app_conversation_info_service,
            get_httpx_client,
            get_sandbox_service,
        )
        from openhands.app_server.services.injector import InjectorState
        from openhands.app_server.user.specifiy_user_context import (
            ADMIN,
            USER_CONTEXT_ATTR,
        )

        try:
            # Create injector state for dependency injection
            state = InjectorState()
            setattr(state, USER_CONTEXT_ATTR, ADMIN)

            async with (
                get_app_conversation_info_service(
                    state
                ) as app_conversation_info_service,
                get_sandbox_service(state) as sandbox_service,
                get_httpx_client(state) as httpx_client,
            ):
                # Get conversation info to find the sandbox
                app_conversation_info = (
                    await app_conversation_info_service.get_app_conversation_info(
                        conversation_id
                    )
                )
                if not app_conversation_info:
                    _logger.error(
                        f'[GitHub V1] Conversation not found: {conversation_id}'
                    )
                    return EventCallbackResult(
                        status=EventCallbackResultStatus.ERROR,
                        event_callback_id=callback.id,
                        event_id=event.id,
                        conversation_id=conversation_id,
                        detail='Conversation not found',
                    )

                # Get sandbox info to find agent server URL
                sandbox = await sandbox_service.get_sandbox(
                    app_conversation_info.sandbox_id
                )
                if not sandbox or sandbox.status != SandboxStatus.RUNNING:
                    _logger.error(
                        f'[GitHub V1] Sandbox not running: {app_conversation_info.sandbox_id}'
                    )
                    return EventCallbackResult(
                        status=EventCallbackResultStatus.ERROR,
                        event_callback_id=callback.id,
                        event_id=event.id,
                        conversation_id=conversation_id,
                        detail='Sandbox not running',
                    )

                # Get agent server URL
                agent_server_url = self._get_agent_server_url(sandbox)

                # Prepare message based on agent state
                message_content = 'Summarize your work'

                # Validate session API key
                if not sandbox.session_api_key:
                    _logger.error(
                        f'[GitHub V1] No session API key for sandbox: {sandbox.id}'
                    )
                    return EventCallbackResult(
                        status=EventCallbackResultStatus.ERROR,
                        event_callback_id=callback.id,
                        event_id=event.id,
                        conversation_id=conversation_id,
                        detail='No session API key available',
                    )

                # Send message to agent server
                await self._send_message_to_agent_server(
                    httpx_client=httpx_client,
                    agent_server_url=agent_server_url,
                    conversation_id=conversation_id,
                    session_api_key=sandbox.session_api_key,
                    message_content=message_content,
                )

                return EventCallbackResult(
                    status=EventCallbackResultStatus.SUCCESS,
                    event_callback_id=callback.id,
                    event_id=event.id,
                    conversation_id=conversation_id,
                )

        except Exception as e:
            _logger.exception(f'[GitHub V1] Error processing callback: {e}')
            return EventCallbackResult(
                status=EventCallbackResultStatus.ERROR,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                detail=str(e),
            )

    def _get_agent_server_url(self, sandbox) -> str:
        """Get agent server URL for running sandbox."""
        exposed_urls = sandbox.exposed_urls
        assert exposed_urls is not None
        agent_server_url = next(
            exposed_url.url
            for exposed_url in exposed_urls
            if exposed_url.name == AGENT_SERVER
        )
        agent_server_url = replace_localhost_hostname_for_docker(agent_server_url)
        return agent_server_url

    async def _send_message_to_agent_server(
        self,
        httpx_client: httpx.AsyncClient,
        agent_server_url: str,
        conversation_id: UUID,
        session_api_key: str,
        message_content: str,
    ) -> None:
        """Send a message to the agent server via the V1 API."""
        # Prepare the message request
        send_message_request = SendMessageRequest(
            role='user',
            content=[TextContent(text=message_content)],
            run=True,  # Automatically run the agent after sending the message
        )

        # Send the message to the agent server
        url = (
            f'{agent_server_url.rstrip("/")}/api/conversations/{conversation_id}/events'
        )
        headers = {'X-Session-API-Key': session_api_key}
        payload = send_message_request.model_dump()

        _logger.debug(f'[GitHub V1] Sending message to {url} with payload: {payload}')

        try:
            response = await httpx_client.post(
                url,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()

            _logger.info(
                f'[GitHub V1] Successfully sent message to conversation {conversation_id}'
            )
        except httpx.HTTPStatusError as e:
            error_detail = f'HTTP {e.response.status_code} error'
            try:
                # Try to get more detailed error information from response body
                error_body = e.response.text
                if error_body:
                    error_detail += f': {error_body}'
            except Exception:
                # If we can't read the response body, just use the basic error
                pass

            _logger.error(
                f'[GitHub V1] HTTP error sending message to {url}: {error_detail}. '
                f'Request payload: {payload}. Response headers: {dict(e.response.headers)}',
                exc_info=True,
            )
            raise httpx.HTTPStatusError(
                f'Failed to send message to agent server: {error_detail}',
                request=e.request,
                response=e.response,
            ) from e
        except httpx.TimeoutException as e:
            error_detail = f'Request timeout after 30 seconds to {url}'
            _logger.error(
                f'[GitHub V1] {error_detail}. Request payload: {payload}', exc_info=True
            )
            raise httpx.TimeoutException(error_detail) from e
        except httpx.RequestError as e:
            error_detail = f'Request error to {url}: {str(e)}'
            _logger.error(
                f'[GitHub V1] {error_detail}. Request payload: {payload}', exc_info=True
            )
            raise httpx.RequestError(error_detail) from e
