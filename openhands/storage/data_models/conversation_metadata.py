from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: int
    selected_repository: str | None
    title: str | None = None
    last_updated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
