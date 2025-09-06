from sqlalchemy import Column, DateTime, Integer, String, text
from storage.base import Base


class LinearConversation(Base):  # type: ignore
    __tablename__ = 'linear_conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, nullable=False, index=True)
    issue_id = Column(String, nullable=False, index=True)
    issue_key = Column(String, nullable=False, index=True)
    parent_id = Column(String, nullable=True)
    linear_user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
