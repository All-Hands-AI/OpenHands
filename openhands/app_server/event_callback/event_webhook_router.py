"""Event Callback router for OpenHands Server."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from openhands.agent_server.models import StoredConversation, Success
from openhands.app_server.dependency import get_dependency_resolver
from openhands.app_server.event.event_service import EventService
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
)
from openhands.app_server.sandbox.sandbox_models import SandboxInfo
from openhands.app_server.sandbox.sandbox_service import SandboxService
from openhands.sdk import EventBase

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
    conversation_info: StoredConversation,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
):
    """Webhook callback for when a conversation starts, pauses, resumes, or deletes."""

    # TODO: Make sure that we have an entry saved for the conversation info.
    #       (We will still go back to the sandbox to determine its status,
    #       but we want the metrics.)


@router.post('/{sandbox_id}/events/{conversation_id}')
async def on_event(
    events: list[EventBase],
    conversation_id: UUID,
    sandbox_info: SandboxInfo = Depends(valid_sandbox),
    event_service: EventService = event_service_dependency,
    event_callback_service: EventCallbackService = event_callback_service_dependency,
) -> Success:
    """Webhook callback for when event stream events occur."""
    # TODO: Before saving events, we should guarantee that the conversation either
    # does not yet exist or is associated with the owner of the sandbox
    try:
        # Save events...
        await asyncio.gather(
            *[event_service.save_event(conversation_id, event) for event in events]
        )

        # Run all callbacks in the background
        for event in events:
            asyncio.create_task(
                event_callback_service.execute_callbacks(conversation_id, event)
            )
    except Exception as exc:
        _logger.exception('Error in webhook', stack_info=True)

    return Success()
