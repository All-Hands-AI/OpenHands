"""Sandboxed Conversation router for OpenHands Server."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openhands.app_server.conversation.conversation_models import (
    SandboxedConversation,
    SandboxedConversationPage,
    StartSandboxedConversationRequest,
)
from openhands.app_server.conversation.sandboxed_conversation_service import (
    SandboxedConversationService,
)
from openhands.app_server.dependency import get_dependency_resolver

router = APIRouter(prefix='/sandboxed-conversations', tags=['Conversations'])
sandboxed_conversation_service_dependency = Depends(
    get_dependency_resolver().sandboxed_conversation.get_resolver_for_user()
)

# Read methods


@router.get('/search')
async def search_sandboxed_conversations(
    title__contains: Annotated[
        str | None,
        Query(title='Filter by title containing this string'),
    ] = None,
    created_at__gte: Annotated[
        datetime | None,
        Query(title='Filter by created_at greater than or equal to this datetime'),
    ] = None,
    created_at__lt: Annotated[
        datetime | None,
        Query(title='Filter by created_at less than this datetime'),
    ] = None,
    updated_at__gte: Annotated[
        datetime | None,
        Query(title='Filter by updated_at greater than or equal to this datetime'),
    ] = None,
    updated_at__lt: Annotated[
        datetime | None,
        Query(title='Filter by updated_at less than this datetime'),
    ] = None,
    page_id: Annotated[
        str | None,
        Query(title='Optional next_page_id from the previously returned page'),
    ] = None,
    limit: Annotated[
        int,
        Query(
            title='The max number of results in the page',
            gt=0,
            lte=100,
        ),
    ] = 100,
    sandboxed_conversation_service: SandboxedConversationService = (
        sandboxed_conversation_service_dependency
    ),
) -> SandboxedConversationPage:
    """Search / List sandboxed conversations."""
    assert limit > 0
    assert limit <= 100
    return await sandboxed_conversation_service.search_sandboxed_conversations(
        title__contains=title__contains,
        created_at__gte=created_at__gte,
        created_at__lt=created_at__lt,
        updated_at__gte=updated_at__gte,
        updated_at__lt=updated_at__lt,
        page_id=page_id,
        limit=limit,
    )


@router.get('/count')
async def count_sandboxed_conversations(
    title__contains: Annotated[
        str | None,
        Query(title='Filter by title containing this string'),
    ] = None,
    created_at__gte: Annotated[
        datetime | None,
        Query(title='Filter by created_at greater than or equal to this datetime'),
    ] = None,
    created_at__lt: Annotated[
        datetime | None,
        Query(title='Filter by created_at less than this datetime'),
    ] = None,
    updated_at__gte: Annotated[
        datetime | None,
        Query(title='Filter by updated_at greater than or equal to this datetime'),
    ] = None,
    updated_at__lt: Annotated[
        datetime | None,
        Query(title='Filter by updated_at less than this datetime'),
    ] = None,
    sandboxed_conversation_service: SandboxedConversationService = (
        sandboxed_conversation_service_dependency
    ),
) -> int:
    """Count sandboxed conversations matching the given filters."""
    return await sandboxed_conversation_service.count_sandboxed_conversations(
        title__contains=title__contains,
        created_at__gte=created_at__gte,
        created_at__lt=created_at__lt,
        updated_at__gte=updated_at__gte,
        updated_at__lt=updated_at__lt,
    )


@router.get('/{id}', responses={404: {'description': 'Item not found'}})
async def get_sandboxed_conversation(
    id: UUID,
    sandboxed_conversation_service: SandboxedConversationService = (
        sandboxed_conversation_service_dependency
    ),
) -> SandboxedConversation:
    """Get a sandboxed conversation given an id."""
    sandboxed_conversation = (
        await sandboxed_conversation_service.get_sandboxed_conversation(id)
    )
    if sandboxed_conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return sandboxed_conversation


@router.get('/')
async def batch_get_sandboxed_conversations(
    ids: Annotated[list[UUID], Query()],
    sandboxed_conversation_service: SandboxedConversationService = (
        sandboxed_conversation_service_dependency
    ),
) -> list[SandboxedConversation | None]:
    """Get a batch of sandboxed conversations given their ids. Return None for any missing."""
    assert len(ids) < 100
    sandboxed_conversations = (
        await sandboxed_conversation_service.batch_get_sandboxed_conversations(ids)
    )
    return sandboxed_conversations


@router.post('/')
async def start_sandboxed_conversation(
    request: StartSandboxedConversationRequest,
    sandboxed_conversation_service: SandboxedConversationService = (
        sandboxed_conversation_service_dependency
    ),
) -> SandboxedConversation:
    return await sandboxed_conversation_service.start_sandboxed_conversation(request)
