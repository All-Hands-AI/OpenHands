from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: str | None
    selected_repository: str | None
    user_id: str | None = None
    selected_branch: str | None = None
    title: str | None = None
    last_updated_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
