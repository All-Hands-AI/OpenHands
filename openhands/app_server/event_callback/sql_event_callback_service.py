# pyright: reportArgumentType=false
"""SQL implementation of EventCallbackService."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from openhands.app_server.event_callback.event_callback_models import (
    CreateEventCallbackRequest,
    EventCallback,
    EventCallbackPage,
    EventKind,
)
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from openhands.app_server.event_callback.event_callback_service import (
    EventCallbackService,
    EventCallbackServiceManager,
)
from openhands.sdk import Event

_logger = logging.getLogger(__name__)


@dataclass
class SQLEventCallbackService(EventCallbackService):
    """SQL implementation of EventCallbackService."""

    session: AsyncSession

    async def create_event_callback(
        self, request: CreateEventCallbackRequest
    ) -> EventCallback:
        """Create a new event callback."""
        # Create EventCallback from request
        event_callback = EventCallback(
            conversation_id=request.conversation_id,
            processor=request.processor,
            event_kind=request.event_kind,
        )

        # Add to session and commit
        await self.session.add(event_callback)
        return event_callback

    async def get_event_callback(self, id: UUID) -> EventCallback | None:
        """Get a single event callback, returning None if not found."""
        stmt = select(EventCallback).where(EventCallback.id == id)
        result = await self.session.execute(stmt)
        stored_callback = result.scalar_one_or_none()
        return stored_callback

    async def delete_event_callback(self, id: UUID) -> bool:
        """Delete an event callback, returning True if deleted, False if not found."""
        stmt = select(EventCallback).where(EventCallback.id == id)
        result = await self.session.execute(stmt)
        stored_callback = result.scalar_one_or_none()

        if stored_callback is None:
            return False

        await self.session.delete(stored_callback)
        return True

    async def search_event_callbacks(
        self,
        conversation_id__eq: UUID | None = None,
        event_kind__eq: EventKind | None = None,
        event_id__eq: UUID | None = None,
        page_id: str | None = None,
        limit: int = 100,
    ) -> EventCallbackPage:
        """Search for event callbacks, optionally filtered by parameters."""
        # Build the query with filters
        conditions = []

        if conversation_id__eq is not None:
            conditions.append(EventCallback.conversation_id == conversation_id__eq)

        if event_kind__eq is not None:
            conditions.append(EventCallback.event_kind == event_kind__eq)

        # Note: event_id__eq is not stored in the event_callbacks table
        # This parameter might be used for filtering results after retrieval
        # or might be intended for a different use case

        # Build the base query
        stmt = select(EventCallback)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Handle pagination
        if page_id is not None:
            # Parse page_id to get offset or cursor
            try:
                offset = int(page_id)
                stmt = stmt.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        stmt = stmt.limit(limit + 1).order_by(EventCallback.created_at.desc())  # type: ignore

        result = await self.session.execute(stmt)
        stored_callbacks = result.scalars().all()

        # Check if there are more results
        has_more = len(stored_callbacks) > limit
        if has_more:
            stored_callbacks = stored_callbacks[:limit]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        return EventCallbackPage(items=stored_callbacks, next_page_id=next_page_id)

    async def execute_callbacks(self, conversation_id: UUID, event: Event) -> None:
        query = (
            select(EventCallback)
            .where(
                or_(
                    EventCallback.event_kind == event.kind,
                    EventCallback.event_kind.is_(None),  # type: ignore
                )
            )
            .where(
                or_(
                    EventCallback.conversation_id == conversation_id,
                    EventCallback.conversation_id.is_(None),  # type: ignore
                )
            )
        )
        callbacks = list(await self.session.execute(query))
        if callbacks:
            await asyncio.gather(
                *[
                    self.execute_callback(conversation_id, callback, event)
                    for callback in callbacks
                ]
            )

    async def execute_callback(
        self, conversation_id: UUID, callback: EventCallback, event: Event
    ):
        try:
            result = await callback.processor(conversation_id, callback, event)
        except Exception as exc:
            _logger.exception(f'Exception in callback {callback.id}', stack_info=True)
            result = EventCallbackResult(
                status=EventCallbackResultStatus.ERROR,
                event_callback_id=callback.id,
                event_id=event.id,
                conversation_id=conversation_id,
                detail=str(exc),
            )
        await self.session.add(result)

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Stop using this event callback service."""
        pass


class SQLEventCallbackServiceManager(EventCallbackServiceManager):
    def get_unsecured_resolver(self) -> Callable:
        from openhands.app_server.config import db_service

        def resolve(
            db_session = Depends(db_service().managed_session_dependency)
        ) -> EventCallbackService:
            return SQLEventCallbackService(db_session)

        return resolve

    def get_resolver_for_current_user(self) -> Callable:
        _logger.warning(
            'Using secured EventCallbackService resolver - '
            'returning unsecured resolver for now. Eventually filter by conversation'
        )
        return self.get_unsecured_resolver()
