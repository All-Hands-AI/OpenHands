from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ConversationTrigger(Enum):
    RESOLVER = 'resolver'
    GUI = 'gui'
    SUGGESTED_TASK = 'suggested_task'
    REMOTE_API_KEY = 'openhands_api'


@dataclass
class ConversationMetadata:
    conversation_id: str
    github_user_id: str | None
    selected_repository: str | None
    user_id: str | None = None
    selected_branch: str | None = None
    title: str | None = None
    last_updated_at: datetime | None = None
    trigger: ConversationTrigger | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Cost and token metrics
    accumulated_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
