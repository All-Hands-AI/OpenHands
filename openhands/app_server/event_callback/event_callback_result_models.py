from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from openhands.agent_server.utils import utc_now
from openhands.sdk.event.types import EventID


class EventCallbackResultStatus(Enum):
    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'


class EventCallbackResultSortOrder(Enum):
    CREATED_AT = 'CREATED_AT'
    CREATED_AT_DESC = 'CREATED_AT_DESC'


class EventCallbackResult(BaseModel):
    """Object representing the result of an event callback."""

    id: UUID = Field(default_factory=uuid4)
    status: EventCallbackResultStatus
    event_callback_id: UUID
    event_id: EventID
    conversation_id: UUID
    detail: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class EventCallbackResultPage(BaseModel):
    items: list[EventCallbackResult]
    next_page_id: str | None = None
