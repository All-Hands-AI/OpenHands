from dataclasses import dataclass
from datetime import datetime

from openhands.server.data_models.conversation_status import ConversationStatus


@dataclass
class ConversationInfo:
    id: str
    title: str | None = None
    last_updated_at: datetime | None = None
    status: ConversationStatus = ConversationStatus.STOPPED
