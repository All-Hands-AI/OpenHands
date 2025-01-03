from dataclasses import dataclass
from datetime import datetime

from openhands.storage.data_models.conversation_status import ConversationStatus


@dataclass
class ConversationInfo:
    """Information about a conversation"""

    conversation_id: str
    title: str
    last_updated_at: datetime | None = None
    status: ConversationStatus = ConversationStatus.STOPPED
    selected_repository: str | None = None
