from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel

from openhands.sdk.event.types import EventID
from openhands.app_server.utils.date_utils import utc_now


class EventCallbackResultStatus(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class EventCallbackResultSortOrder(Enum):
    CREATED_AT = "CREATED_AT"
    CREATED_AT_DESC = "CREATED_AT_DESC"


class EventCallbackResult(SQLModel, table=True): # type ignore
    """Object representing the result of an event callback."""

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    status: EventCallbackResultStatus = SQLField(index=True)
    event_callback_id: UUID = SQLField(index=True)
    event_id: EventID = SQLField(index=True)
    conversation_id: UUID = SQLField(index=True)
    detail: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class EventCallbackResultPage(BaseModel):
    items: list[EventCallbackResult]
    next_page_id: str | None = None
