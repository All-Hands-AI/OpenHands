from sqlalchemy import Column, DateTime, String, text
from storage.base import Base


class StoredOfflineToken(Base):
    __tablename__ = 'offline_tokens'

    user_id = Column(String(255), primary_key=True)
    offline_token = Column(String, nullable=False)
    created_at = Column(
        DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
