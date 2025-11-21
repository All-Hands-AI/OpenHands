import logging
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

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
from openhands.core.schema.agent import AgentState
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.sdk import Event
from openhands.sdk.event import ConversationStateUpdateEvent


class TextContent(BaseModel):
    """Text content for messages."""

    type: Literal['text'] = 'text'
    text: str


class SendMessageRequest(BaseModel):
    """Payload to send a message to the agent.

    This is a simplified version of the SDK's SendMessageRequest.
    """

    role: Literal['user', 'system', 'assistant', 'tool'] = 'user'
    content: list[TextContent] = Field(default_factory=list)
    run: bool = Field(
        default=False,
        description='Whether the agent loop should automatically run if not running',
    )


_logger = logging.getLogger(__name__)


class GithubV1CallbackProcessor(EventCallbackProcessor):
    """Callback processor for GitHub V1 integrations."""

    github_view_data: dict = Field(default_factory=dict)
    send_summary_instruction: bool = Field(default=True)

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

        if event.key != "execution_status" and event.value != "finished":
            return None

        _logger.info(f'[GitHub V1] Callback agent state was {event}')

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
                message_content = "Summarize your work"

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
            role='system',
            content=[TextContent(text=message_content)],
            run=False,  # Don't automatically run the agent
        )

        # Send the message to the agent server
        url = (
            f'{agent_server_url.rstrip("/")}/api/conversations/{conversation_id}/events'
        )
        headers = {'X-Session-API-Key': session_api_key}

        response = await httpx_client.post(
            url,
            json=send_message_request.model_dump(),
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()

        _logger.info(
            f'[GitHub V1] Successfully sent message to conversation {conversation_id}'
        )
