# pyright: reportIncompatibleMethodOverride=false
# Disable for this file because SQLModel confuses pyright
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from pydantic import Field
from sqlalchemy import JSON, Column, DateTime, String, func
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from openhands.agent_server.utils import utc_now
from openhands.app_server.event_callback.event_callback_result_models import (
    EventCallbackResult,
    EventCallbackResultStatus,
)
from openhands.sdk import Event
from openhands.sdk.utils.models import (
    DiscriminatedUnionMixin,
    OpenHandsModel,
    get_known_concrete_subclasses,
)

_logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    EventKind = str
else:
    EventKind = Literal[
        tuple(c.__name__ for c in get_known_concrete_subclasses(Event))
    ]


class EventCallbackProcessor(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult:
        """Process an event."""


class LoggingCallbackProcessor(EventCallbackProcessor):
    """Example implementation which logs callbacks."""

    async def __call__(
        self,
        conversation_id: UUID,
        callback: EventCallback,
        event: Event,
    ) -> EventCallbackResult:
        _logger.info(f'Callback {callback.id} Invoked for event {event}')
        return EventCallbackResult(
            status=EventCallbackResultStatus.SUCCESS,
            event_callback_id=callback.id,
            event_id=event.id,
            conversation_id=conversation_id,
        )


class CreateEventCallbackRequest(OpenHandsModel):
    conversation_id: UUID | None = Field(
        default=None,
        description=(
            'Optional filter on the conversation to which this callback applies'
        ),
    )
    processor: EventCallbackProcessor = SQLField(sa_column=Column(JSON))
    event_kind: EventKind | None = SQLField(
        default=None,
        description=(
            'Optional filter on the type of events to which this callback applies'
        ),
        sa_column=Column(String),
    )


class EventCallback(SQLModel, CreateEventCallbackRequest, table=True):  # type: ignore
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    created_at: datetime = SQLField(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))


class EventCallbackPage(OpenHandsModel):
    items: list[EventCallback]
    next_page_id: str | None = None
