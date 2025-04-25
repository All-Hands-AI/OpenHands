from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ConversationTrigger(Enum):
    RESOLVER = 'resolver'
    GUI = 'gui'


class CommitState(str, Enum):
    """Enum representing the state of git commits in a repository."""
    CLEAN = "CLEAN"  # No changes, current commit matches origin commit for the same branch
    IN_PROGRESS = "IN_PROGRESS"  # There are uncommitted changes or local commits not in origin


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
    # Git state
    commit_state: CommitState | None = None
    # Cost and token metrics
    accumulated_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
