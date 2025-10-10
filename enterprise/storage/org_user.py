"""
SQLAlchemy model for Organization-User relationship.
"""

from pydantic import SecretStr
from sqlalchemy import UUID, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from enterprise.storage.base import Base
from enterprise.storage.encrypt_utils import decrypt_value, encrypt_value


class OrgUser(Base):  # type: ignore
    """Junction table for organization-user relationships with roles."""

    __tablename__ = 'org_user'

    org_id = Column(UUID(as_uuid=True), ForeignKey('org.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    _llm_api_key = Column(String, nullable=False)
    status = Column(String, nullable=True)

    # Relationships
    org = relationship('Org', back_populates='org_users')
    user = relationship('User', back_populates='org_users')
    role = relationship('Role', back_populates='org_users')

    def __init__(self, **kwargs):
        # Handle known SQLAlchemy columns directly
        for key in list(kwargs):
            if hasattr(self.__class__, key):
                setattr(self, key, kwargs.pop(key))

        # Handle custom property-style fields
        if 'llm_api_key' in kwargs:
            self.llm_api_key = kwargs.pop('llm_api_key')

        if kwargs:
            raise TypeError(f'Unexpected keyword arguments: {list(kwargs.keys())}')

    @property
    def llm_api_key(self) -> SecretStr:
        decrypted = decrypt_value(self._llm_api_key)
        return SecretStr(decrypted)

    @llm_api_key.setter
    def llm_api_key(self, value: str | SecretStr):
        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        self._llm_api_key = encrypt_value(raw)
