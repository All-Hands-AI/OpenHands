from sqlalchemy import BigInteger, Column, Identity, Index, Integer, String
from storage.base import Base


class AuthTokens(Base):  # type: ignore
    __tablename__ = 'auth_tokens'
    id = Column(Integer, Identity(), primary_key=True)
    keycloak_user_id = Column(String, nullable=False, index=True)
    identity_provider = Column(String, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    access_token_expires_at = Column(
        BigInteger, nullable=False
    )  # Time since epoch in seconds
    refresh_token_expires_at = Column(
        BigInteger, nullable=False
    )  # Time since epoch in seconds

    __table_args__ = (
        Index(
            'idx_auth_tokens_keycloak_user_identity_provider',
            'keycloak_user_id',
            'identity_provider',
            unique=True,
        ),
    )
