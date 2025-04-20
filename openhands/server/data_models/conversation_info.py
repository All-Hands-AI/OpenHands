from dataclasses import dataclass, field
from datetime import datetime, timezone

from openhands.integrations.service_types import Repository
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
    # Legacy string representation of repository, kept for backward compatibility
    # See also: https://github.com/All-Hands-AI/OpenHands/issues/7286
    selected_repository: str | None = None
    selected_repository_model: Repository | None = None
    trigger: ConversationTrigger | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_selected_repository_full_name(self) -> str | None:
        if self.selected_repository_model is not None:
            return self.selected_repository_model.full_name
        elif self.selected_repository is not None:
            return self.selected_repository
        else:
            return None
