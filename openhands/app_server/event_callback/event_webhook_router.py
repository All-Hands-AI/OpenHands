"""Event Callback router for OpenHands Server."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from sqlalchemy.ext.asyncio import AsyncSession

from openhands.agent_server.models import ConversationInfo, Success
from openhands.app_server.app_conversation.app_conversation_info_service import AppConversationInfoService
from openhands.app_server.app_conversation.app_conversation_models import AppConversationInfo
from openhands.app_server.database import unmanaged_session_dependency
from openhands.app_server.dependency import get_dependency_resolver
from openhands.app_server.errors import AuthError
from openhands.app_server.event.event_service import EventService
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
)
from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.sdk import Event

router = APIRouter(prefix='/event-webhooks', tags=['Event Callbacks'])
sandbox_service_dependency = Depends(
    get_dependency_resolver().sandbox.get_unsecured_resolver()
)
event_service_dependency = Depends(
    get_dependency_resolver().event.get_unsecured_resolver()
)
event_callback_service_dependency = Depends(
    get_dependency_resolver().event_callback.get_unsecured_resolver()
)
app_conversation_info_service_dependency = Depends(
    get_dependency_resolver().app_conversation_info.get_unsecured_resolver()
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
    session: AsyncSession = Depends(unmanaged_session_dependency),
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

        asyncio.create_task(_run_callbacks_in_bg_and_close(event_callback_service, conversation_id, events, session))

    except Exception:
        _logger.exception('Error in webhook', stack_info=True)

    return Success()


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
        session.close()
