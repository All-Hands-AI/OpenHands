"""Event Callback router for OpenHands Server."""

import asyncio
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader

from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.agent_server.models import ConversationInfo, Success
from openhands.app_server.app_conversation.app_conversation_info_service import AppConversationInfoService
from openhands.app_server.app_conversation.app_conversation_models import AppConversationInfo
from openhands.app_server.config import app_conversation_info_manager, db_service, event_callback_manager, event_manager, resolve_jwt_service, sandbox_manager, user_admin_manager
from openhands.app_server.errors import AuthError
from openhands.app_server.event.event_service import EventService
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
)
from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.sdk import Event

from openhands.app_server.services.jwt_service import JwtService
from openhands.app_server.user.user_admin_service import UserAdminService
from openhands.integrations.provider import ProviderType

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])
sandbox_service_dependency = Depends(
    sandbox_manager().get_unsecured_resolver()
)
event_service_dependency = Depends(
    event_manager().get_unsecured_resolver()
)
event_callback_service_dependency = Depends(
    event_callback_manager().get_unsecured_resolver()
)
app_conversation_info_service_dependency = Depends(
    app_conversation_info_manager().get_unsecured_resolver()
)
user_admin_service_dependency = Depends(
    user_admin_manager().get_unsecured_resolver()
)
_logger = logging.getLogger(__name__)


async def valid_sandbox(
    sandbox_id: str,
    session_api_key: str = Depends(
        APIKeyHeader(name='X-Session-API-Key', auto_error=False)
    ),
    sandbox_service: SandboxService = sandbox_service_dependency,
) -> SandboxInfo:
    sandbox_info = await sandbox_service.get_sandbox(sandbox_id)
    if sandbox_info is None or sandbox_info.session_api_key != session_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return sandbox_info


@router.post('/{sandbox_id}/conversations')
async def on_conversation_update(
    conversation_info: ConversationInfo,
    app_conversation_info_service: AppConversationInfoService = app_conversation_info_service_dependency,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
) -> Success:
    """Webhook callback for when a conversation starts, pauses, resumes, or deletes."""
    app_conversation = await app_conversation_info_service.get_app_conversation_info(conversation_info.id)
    if app_conversation:
        if app_conversation.created_by_user_id != sandbox_info.created_by_user_id:
            raise AuthError()
    else:
        app_conversation_info = AppConversationInfo(
            id=conversation_info.id,
            title=f'Conversation {conversation_info.id}',
            sandbox_id=sandbox_info.id,
            created_by_user_id=sandbox_info.created_by_user_id,
            llm_model=conversation_info.agent.llm.model,
            # TODO: Lots of git parameters required
        )
        await app_conversation_info_service.save_app_conversation_info(app_conversation_info)

    return Success()


@router.post('/{sandbox_id}/events/{conversation_id}')
async def on_event(
    events: list[Event],
    conversation_id: UUID,
    db_session: AsyncSession = Depends(db_service().unmanaged_session_dependency),
    app_conversation_info_service: AppConversationInfoService = app_conversation_info_service_dependency,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
    event_service: EventService = event_service_dependency,
    event_callback_service: EventCallbackService = event_callback_service_dependency,
) -> Success:
    """Webhook callback for when event stream events occur."""

    # Events can only be applied to an exsiting conversation with the correct owner
    app_conversation = await app_conversation_info_service.get_app_conversation_info(conversation_id)
    if not app_conversation or app_conversation.created_by_user_id != sandbox_info.created_by_user_id:
        raise AuthError()

    try:
        # Save events...
        await asyncio.gather(
            *[event_service.save_event(conversation_id, event) for event in events]
        )

        asyncio.create_task(_run_callbacks_in_bg_and_close(event_callback_service, conversation_id, events, db_session))

    except Exception:
        _logger.exception('Error in webhook', stack_info=True)

    return Success()


@router.get('/secrets')
async def get_secret(
    access_token: str = Depends(
        APIKeyHeader(name='X-Access-Token', auto_error=False)
    ),
    jwt_service: JwtService = Depends(resolve_jwt_service),
    user_admin_service: UserAdminService = app_conversation_info_service_dependency,
) -> str:
    """ Given an access token, retrieve a user secret. The access token
    is limited by user and provider type, and may include a timeout, limiting
    the damage in the event that a token is ever leaked """
    try:
        payload = jwt_service.verify_jws_token(access_token)
        user_id = payload['user_id']
        provider_type = ProviderType[payload['provider_type']]
        user_service = await user_admin_service.get_user_service(user_id)
        secret = None
        if user_service:
            secret = await user_service.get_latest_token(provider_type)
        if secret is None:
            raise HTTPException(404, "No such provider")
        return secret
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


async def _run_callbacks_in_bg_and_close(
    event_callback_service: EventCallbackService,
    conversation_id: UUID,
    events: list[Event],
    session: AsyncSession,
):
    """ Run all callbacks and close the session"""
    try:
        # We don't use asynio.gather here because callbacks must be run in sequence.
        for event in events:
            await event_callback_service.execute_callbacks(conversation_id, event)
    finally:
        await session.close()
