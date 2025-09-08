from sqlalchemy import Column, DateTime, Identity, Integer, String, text
from storage.base import Base


class SlackTeam(Base):  # type: ignore
    __tablename__ = 'slack_teams'
    id = Column(Integer, Identity(), primary_key=True)
    team_id = Column(String, nullable=False, index=True, unique=True)
    bot_access_token = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False,
    )
