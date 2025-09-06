from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func
from storage.base import Base


class Feedback(Base):  # type: ignore
    __tablename__ = 'feedback'

    id = Column(String, primary_key=True)
    version = Column(String, nullable=False)
    email = Column(String, nullable=False)
    polarity = Column(
        Enum('positive', 'negative', name='polarity_enum'), nullable=False
    )
    permissions = Column(
        Enum('public', 'private', name='permissions_enum'), nullable=False
    )
    trajectory = Column(JSON, nullable=True)


class ConversationFeedback(Base):  # type: ignore
    __tablename__ = 'conversation_feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, nullable=False, index=True)
    event_id = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
