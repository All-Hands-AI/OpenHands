"""Sandboxed Conversation router for OpenHands Server."""

import asyncio
from datetime import datetime
from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversation,
    AppConversationPage,
    AppConversationStartRequest,
    AppConversationStartTask,
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


@router.get('')
async def batch_get_app_conversations(
    ids: Annotated[list[UUID], Query()],
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> list[AppConversation | None]:
    """Get a batch of sandboxed conversations given their ids. Return None for any missing."""
    assert len(ids) < 100
    app_conversations = await app_conversation_service.batch_get_app_conversations(ids)
    return app_conversations


@router.post('')
async def start_app_conversation(
    request: AppConversationStartRequest,
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> AppConversationStartTask:
    """ Start an app conversation start task and return it."""
    async_iter = app_conversation_service.start_app_conversation(request)
    result = await anext(async_iter)
    asyncio.create_task(_consume_remaining(async_iter))
    return result


@router.post('/stream-start')
async def stream_app_conversation_start(
    request: AppConversationStartRequest,
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> list[AppConversationStartTask]:
    """ Start an app conversation start task and stream updates from it.
    Leaves the connection open until either the conversation starts or there was an error"""
    response = StreamingResponse(_stream_app_conversation_start(request, app_conversation_service), media_type="application/json")
    return response


@router.get('/start-tasks')
async def batch_get_app_conversation_start_tasks(
    ids: Annotated[list[UUID], Query()],
    app_conversation_service: AppConversationService = (
        app_conversation_service_dependency
    ),
) -> list[AppConversationStartTask | None]:
    """Get a batch of start app conversation tasks given their ids. Return None for any missing."""
    assert len(ids) < 100
    start_tasks = await app_conversation_service.batch_get_app_conversation_start_tasks(
        ids
    )
    return start_tasks


async def _consume_remaining(async_iter):
    """Consume the remaining items from an async iterator"""
    try:
        while True:
            await anext(async_iter)
    except StopAsyncIteration:
        return

async def _stream_app_conversation_start(
    request: AppConversationStartRequest,
    app_conversation_service: AppConversationService
) -> AsyncGenerator[str, None]:
    """Stream a json list, item by item."""
    yield '[\n'
    comma = False
    async for task in app_conversation_service.start_app_conversation(request):
        chunk = task.model_dump_json()
        if comma:
            chunk = ',\n' + chunk
        comma = True
        yield chunk
    yield ']'
