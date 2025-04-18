from dataclasses import dataclass, field
from datetime import datetime, timezone

from openhands.storage.data_models.conversation_metadata import ConversationTrigger
from openhands.storage.data_models.conversation_status import ConversationStatus


@dataclass
class ConversationInfo:
    """
    Information about a conversation. This combines conversation metadata with
    information on whether a conversation is currently running
    """

    conversation_id: str
    title: str
    last_updated_at: datetime | None = None
    status: ConversationStatus = ConversationStatus.STOPPED
    selected_repository: str | None = None
    trigger: ConversationTrigger | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
