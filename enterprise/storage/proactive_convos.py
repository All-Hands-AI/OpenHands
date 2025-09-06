from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from storage.base import Base


class ProactiveConversation(Base):
    __tablename__ = 'proactive_conversation_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(String, nullable=False)
    pr_number = Column(Integer, nullable=False)
    workflow_runs = Column(JSON, nullable=False)
    commit = Column(String, nullable=False)
    conversation_starter_sent = Column(Boolean, nullable=False, default=False)
    last_updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
