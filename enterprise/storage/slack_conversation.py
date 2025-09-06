from sqlalchemy import Column, Identity, Integer, String
from storage.base import Base


class SlackConversation(Base):  # type: ignore
    __tablename__ = 'slack_conversation'
    id = Column(Integer, Identity(), primary_key=True)
    conversation_id = Column(String, nullable=False, index=True)
    channel_id = Column(String, nullable=False)
    keycloak_user_id = Column(String, nullable=False)
    parent_id = Column(String, nullable=True, index=True)
