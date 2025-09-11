import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from storage.base import Base


class StoredConversationMetadata(Base):  # type: ignore
    __tablename__ = 'conversation_metadata'
    conversation_id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_user_id = Column(String, nullable=True)  # The GitHub user ID
    user_id = Column(String, nullable=False)  # The Keycloak User ID
    selected_repository = Column(String, nullable=True)
    selected_branch = Column(String, nullable=True)
    git_provider = Column(
        String, nullable=True
    )  # The git provider (GitHub, GitLab, etc.)
    title = Column(String, nullable=True)
    last_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),  # type: ignore[attr-defined]
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),  # type: ignore[attr-defined]
    )
    trigger = Column(String, nullable=True)
    pr_number = Column(
        JSON, nullable=True
    )  # List of PR numbers associated with the conversation

    # Cost and token metrics
    accumulated_cost = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # LLM model used for the conversation
    llm_model = Column(String, nullable=True)
