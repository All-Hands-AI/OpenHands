from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from openhands.agent_server.utils import utc_now
from openhands.sdk.event.types import EventID


class EventCallbackResultStatus(Enum):
    SUCCESS = 'SUCCESS'
    ERROR = 'ERROR'


class EventCallbackResultSortOrder(Enum):
    CREATED_AT = 'CREATED_AT'
    CREATED_AT_DESC = 'CREATED_AT_DESC'


class EventCallbackResult(SQLModel, table=True):  # type: ignore
    """Object representing the result of an event callback."""

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    status: EventCallbackResultStatus = SQLField(index=True)
    event_callback_id: UUID = SQLField(index=True)
    event_id: EventID = SQLField(index=True)
    conversation_id: UUID = SQLField(index=True)
    detail: str | None = None
    created_at: datetime = SQLField(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True))


class EventCallbackResultPage(BaseModel):
    items: list[EventCallbackResult]
    next_page_id: str | None = None
