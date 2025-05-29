from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.conversation_metadata import ConversationTrigger
from openhands.storage.data_models.conversation_status import ConversationStatus


@dataclass
class RepositoryInfo:
    """
    Information about a repository associated with a conversation
    """

    full_name: str | None = None
    id: int | None = None
    git_provider: ProviderType | None = None
    is_public: bool | None = None


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
    trigger: ConversationTrigger | None = None
    num_connections: int = 0
    url: str | None = None
    session_api_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Repository information
    repository: Optional[RepositoryInfo] = None
