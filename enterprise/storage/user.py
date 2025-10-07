"""
SQLAlchemy model for User.
"""

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from enterprise.storage.base import Base


class User(Base):  # type: ignore
    """User model with organizational relationships."""

    __tablename__ = 'user'

    id = Column(Integer, Identity(), primary_key=True)
    keycloak_user_id = Column(String, nullable=False, unique=True, index=True)
    current_org_id = Column(UUID(as_uuid=True), ForeignKey('org.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=True)
    accepted_tos = Column(DateTime, nullable=True)
    enable_sound_notifications = Column(Boolean, nullable=True)
    language = Column(String, nullable=True)
    user_consents_to_analytics = Column(Boolean, nullable=True)
    email = Column(String, nullable=True)
    email_verified = Column(Boolean, nullable=True)

    # Relationships
    role = relationship('Role', back_populates='users')
    org_users = relationship('OrgUser', back_populates='user')
    current_org = relationship('Org', back_populates='current_users')
