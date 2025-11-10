from datetime import UTC, datetime

from sqlalchemy import Column, Float, Index, Integer, String
from storage.base import Base


class ConversationWork(Base):  # type: ignore
    __tablename__ = 'conversation_work'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    seconds = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        String, default=lambda: datetime.now(UTC).isoformat(), nullable=False
    )
    updated_at = Column(
        String,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
        nullable=False,
    )

    # Create composite index for efficient queries
    __table_args__ = (
        Index('ix_conversation_work_user_conversation', 'user_id', 'conversation_id'),
    )
