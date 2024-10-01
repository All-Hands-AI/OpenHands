from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID, uuid4

from oh.event.detail.event_detail_abc import EventDetailABC


T = TypeVar("T", bound=EventDetailABC)


@dataclass
class OhEvent(Generic[T]):
    """
    Class representing some event that occurred within and OpenHands Process that may be
    interest externally. For example: TaskCompleted
    """

    conversation_id: UUID
    detail: T
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    handled_at: Optional[datetime] = None

    def dump() -> str:
        # Dump this event to an external format.
        raise ValueError("not_implemented")
