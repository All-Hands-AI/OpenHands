from sqlalchemy import Column, DateTime, Integer, String, text
from storage.base import Base


class JiraUser(Base):  # type: ignore
    __tablename__ = 'jira_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    keycloak_user_id = Column(String, nullable=False, index=True)
    jira_user_id = Column(String, nullable=False, index=True)
    jira_workspace_id = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False)
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
