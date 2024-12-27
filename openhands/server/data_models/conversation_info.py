from dataclasses import dataclass
from datetime import datetime

from openhands.server.data_models.conversation_status import ConversationStatus


@dataclass
class ConversationInfo:
    """Information about a conversation"""

    id: str
    title: str | None = None
    last_updated_at: datetime | None = None
    status: ConversationStatus = ConversationStatus.STOPPED
    selected_repository: str | None = None
