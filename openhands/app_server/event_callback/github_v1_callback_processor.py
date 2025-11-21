import logging
import os
from uuid import UUID

import httpx
from pydantic import Field

from openhands.agent_server.models import SendMessageRequest
from sympy import N
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
from openhands.sdk import Event, TextContent
from openhands.sdk.event import ConversationStateUpdateEvent
from github import Github, GithubIntegration


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

        _logger.info(f'[GitHub V1] Callback event {event}')

        if not isinstance(event, ConversationStateUpdateEvent):
            return None

        if event.key != 'execution_status' and event.value != 'finished':
            return None

        _logger.info(f'[GitHub V1] Callback agent state was {event}')



        if self.send_summary_instruction:
            self.send_summary_instruction = False
            _logger.info(f'[GitHub V1] Sending summary instruction: {conversation_id}')
            return self._send_summary_instruction(
                conversation_id,
                callback,
                event,
            )


        if self.should_extract:
            self.should_extract = False
            summary = self._extract_summary()
            return self._post_summary_to_github(
                summary
            )


    def _get_installation_access_token(
        self,
    ) -> str:
        installation_id = self.github_view_data.get('installation_id')

        if not installation_id:
            raise ValueError(f'Missing installation ID for Github Payload: {self.github_view_data}')

        GITHUB_APP_CLIENT_ID = os.getenv('GITHUB_APP_CLIENT_ID', '').strip()
        GITHUB_APP_PRIVATE_KEY = os.getenv('GITHUB_APP_PRIVATE_KEY', '').replace('\\n', '\n')



        github_integration = GithubIntegration(
            GITHUB_APP_CLIENT_ID, GITHUB_APP_PRIVATE_KEY
        )
        token_data = github_integration.get_access_token(
            installation_id
        )
        return token_data.token



    async def _extract_summary(
        self
    ):
        return ""

    async def _post_summary_to_github(
        self,
        summary: str
    ):
        installation_token = self._get_installation_access_token()

        full_repo_name = self.github_view_data["full_repo_name"]
        issue_number = self.github_view_data["issue_number"]

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
