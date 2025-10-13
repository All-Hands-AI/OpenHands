"""Event Callback router for OpenHands Server."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jwt import InvalidTokenError

from openhands.agent_server.models import ConversationInfo, Success
from openhands.app_server.app_conversation.app_conversation_info_service import (
    AppConversationInfoService,
)
from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
)
from openhands.app_server.config import (
    depends_app_conversation_info_service,
    depends_db_session,
    depends_event_service,
    depends_jwt_service,
    depends_sandbox_service,
    get_event_callback_service,
    get_global_config,
)
from openhands.app_server.errors import AuthError
from openhands.app_server.event.event_service import EventService
from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.app_server.services.injector import InjectorState
from openhands.app_server.services.jwt_service import JwtService
from openhands.app_server.user.specifiy_user_context import (
    USER_CONTEXT_ATTR,
    SpecifyUserContext,
    as_admin,
)
from openhands.app_server.user.user_context import UserContext
from openhands.integrations.provider import ProviderType
from openhands.sdk import Event

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])
sandbox_service_dependency = depends_sandbox_service()
event_service_dependency = depends_event_service()
app_conversation_info_service_dependency = depends_app_conversation_info_service()
jwt_dependency = depends_jwt_service()
config = get_global_config()
db_session_dependency = depends_db_session()
_logger = logging.getLogger(__name__)


async def valid_sandbox(
    sandbox_id: str,
    user_context: UserContext = Depends(as_admin),
    session_api_key: str = Depends(
        APIKeyHeader(name='X-Session-API-Key', auto_error=False)
    ),
    sandbox_service: SandboxService = sandbox_service_dependency,
) -> SandboxInfo:
    sandbox_info = await sandbox_service.get_sandbox(sandbox_id)
    if sandbox_info is None or sandbox_info.session_api_key != session_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return sandbox_info


async def valid_conversation(
    conversation_id: UUID,
    sandbox_info: SandboxInfo,
    app_conversation_info_service: AppConversationInfoService = app_conversation_info_service_dependency,
) -> AppConversationInfo:
    app_conversation_info = (
        await app_conversation_info_service.get_app_conversation_info(conversation_id)
    )
    if not app_conversation_info:
        # Conversation does not yet exist - create a stub
        return AppConversationInfo(
            id=conversation_id,
            sandbox_id=sandbox_info.id,
            created_by_user_id=sandbox_info.created_by_user_id,
        )
    if app_conversation_info.created_by_user_id != sandbox_info.created_by_user_id:
        # Make sure that the conversation and sandbox were created by the same user
        raise AuthError()
    return app_conversation_info


@router.post('/{sandbox_id}/conversations')
async def on_conversation_update(
    conversation_info: ConversationInfo,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
    app_conversation_info_service: AppConversationInfoService = app_conversation_info_service_dependency,
) -> Success:
    """Webhook callback for when a conversation starts, pauses, resumes, or deletes."""
    existing = await valid_conversation(
        conversation_info.id, sandbox_info, app_conversation_info_service
    )

    app_conversation_info = AppConversationInfo(
        id=conversation_info.id,
        # TODO: As of writing, ConversationInfo from AgentServer does not have a title
        title=existing.title or f'Conversation {conversation_info.id}',
        sandbox_id=sandbox_info.id,
        created_by_user_id=sandbox_info.created_by_user_id,
        llm_model=conversation_info.agent.llm.model,
        # Git parameters
        selected_repository=existing.selected_repository,
        selected_branch=existing.selected_branch,
        git_provider=existing.git_provider,
        trigger=existing.trigger,
        pr_number=existing.pr_number,
    )
    await app_conversation_info_service.save_app_conversation_info(
        app_conversation_info
    )

    return Success()


@router.post('/{sandbox_id}/events/{conversation_id}')
async def on_event(
    events: list[Event],
    conversation_id: UUID,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
    app_conversation_info_service: AppConversationInfoService = app_conversation_info_service_dependency,
    event_service: EventService = event_service_dependency,
) -> Success:
    """Webhook callback for when event stream events occur."""

    app_conversation_info = await valid_conversation(
        conversation_id, sandbox_info, app_conversation_info_service
    )

    try:
        # Save events...
        await asyncio.gather(
            *[event_service.save_event(conversation_id, event) for event in events]
        )

        asyncio.create_task(
            _run_callbacks_in_bg_and_close(
                conversation_id, app_conversation_info.created_by_user_id, events
            )
        )

    except Exception:
        _logger.exception('Error in webhook', stack_info=True)

    return Success()


@router.get('/secrets')
async def get_secret(
    access_token: str = Depends(APIKeyHeader(name='X-Access-Token', auto_error=False)),
    jwt_service: JwtService = jwt_dependency,
) -> str:
    """Given an access token, retrieve a user secret. The access token
    is limited by user and provider type, and may include a timeout, limiting
    the damage in the event that a token is ever leaked"""
    try:
        payload = jwt_service.verify_jws_token(access_token)
        user_id = payload['user_id']
        provider_type = ProviderType[payload['provider_type']]
        user_injector = config.user
        assert user_injector is not None
        user_context = await user_injector.get_for_user(user_id)
        secret = None
        if user_context:
            secret = await user_context.get_latest_token(provider_type)
        if secret is None:
            raise HTTPException(404, 'No such provider')
        return secret
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


async def _run_callbacks_in_bg_and_close(
    conversation_id: UUID,
    user_id: str | None,
    events: list[Event],
):
    """Run all callbacks and close the session"""
    state = InjectorState()
    setattr(state, USER_CONTEXT_ATTR, SpecifyUserContext(user_id=user_id))

    async with get_event_callback_service(state) as event_callback_service:
        # We don't use asynio.gather here because callbacks must be run in sequence.
        for event in events:
            await event_callback_service.execute_callbacks(conversation_id, event)
