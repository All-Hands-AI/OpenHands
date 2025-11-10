from sqlalchemy import Column, DateTime, Identity, Integer, String, text
from storage.base import Base


class SlackUser(Base):  # type: ignore
    __tablename__ = 'slack_users'
    id = Column(Integer, Identity(), primary_key=True)
    keycloak_user_id = Column(String, nullable=False, index=True)
    slack_user_id = Column(String, nullable=False, index=True)
    slack_display_name = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
