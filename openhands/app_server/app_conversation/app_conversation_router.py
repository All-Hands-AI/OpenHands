"""Sandboxed Conversation router for OpenHands Server."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversation,
    AppConversationPage,
    StartAppConversationRequest,
)
from openhands.app_server.app_conversation.app_conversation_service import (
    AppConversationService,
)
from openhands.app_server.dependency import get_dependency_resolver

router = APIRouter(prefix='/app-conversations', tags=['Conversations'])
app_conversation_service_dependency = Depends(
    get_dependency_resolver().app_conversation.get_resolver_for_user()
)

# Read methods


@router.get('/search')
async def search_app_conversations(
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
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> AppConversationPage:
    """Search / List sandboxed conversations."""
    assert limit > 0
    assert limit <= 100
    return await app_conversation_service.search_app_conversations(
        title__contains=title__contains,
        created_at__gte=created_at__gte,
        created_at__lt=created_at__lt,
        updated_at__gte=updated_at__gte,
        updated_at__lt=updated_at__lt,
        page_id=page_id,
        limit=limit,
    )


@router.get('/count')
async def count_app_conversations(
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
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> int:
    """Count sandboxed conversations matching the given filters."""
    return await app_conversation_service.count_app_conversations(
        title__contains=title__contains,
        created_at__gte=created_at__gte,
        created_at__lt=created_at__lt,
        updated_at__gte=updated_at__gte,
        updated_at__lt=updated_at__lt,
    )


@router.get('/')
async def batch_get_app_conversations(
    ids: Annotated[list[UUID], Query()],
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> list[AppConversation | None]:
    """Get a batch of sandboxed conversations given their ids. Return None for any missing."""
    assert len(ids) < 100
    app_conversations = (
        await app_conversation_service.batch_get_app_conversations(ids)
    )
    return app_conversations


@router.post('/')
async def start_app_conversation(
    request: StartAppConversationRequest,
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> AppConversation:
    return await app_conversation_service.start_app_conversation(request)
