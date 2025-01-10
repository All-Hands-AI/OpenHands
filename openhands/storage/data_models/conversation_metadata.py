from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: int
    selected_repository: str | None
    title: str | None = None
    last_updated_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
