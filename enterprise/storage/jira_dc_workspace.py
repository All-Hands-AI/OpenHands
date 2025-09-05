from sqlalchemy import Column, DateTime, Integer, String, text
from storage.base import Base


class JiraDcWorkspace(Base):  # type: ignore
    __tablename__ = 'jira_dc_workspaces'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    admin_user_id = Column(String, nullable=False)
    webhook_secret = Column(String, nullable=False)
    svc_acc_email = Column(String, nullable=False)
    svc_acc_api_key = Column(String, nullable=False)
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
