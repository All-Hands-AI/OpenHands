from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from oh.event.detail.event_detail_abc import EventDetailABC
from oh.conversation.conversation_status import ConversationStatus


@dataclass
class ConversationStatusUpdate(EventDetailABC):
    """Event indicating that the status of a conversation has changed"""

    conversation_id: UUID
    status: ConversationStatus
    type: Literal["ConversationStatusUpdate"] = "ConversationStatusUpdate"
