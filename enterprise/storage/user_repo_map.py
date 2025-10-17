from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from storage.base import Base


class UserRepositoryMap(Base):
    """
    Represents a map between user id and repo ids
    """

    __tablename__ = 'user-repos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey('org.id'), nullable=False)
    repo_id = Column(String, nullable=False)
    admin = Column(Boolean, nullable=True)

    # Relationships
    org = relationship('Org', back_populates='user_repos')
