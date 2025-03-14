from datetime import datetime
from typing import Optional
from enum import Enum

class ProviderType(str, Enum):
    GITHUB = "github"
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class ProviderToken:
    """Model for OAuth provider tokens"""
    
    def __init__(self, id: int, user_id: int, provider_type: ProviderType,
                 provider_user_id: Optional[str], access_token: str,
                 refresh_token: Optional[str], expires_at: Optional[datetime],
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.user_id = user_id
        self.provider_type = provider_type
        self.provider_user_id = provider_user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.created_at = created_at
        self.updated_at = updated_at
    
    def is_expired(self) -> bool:
        """Check if the token is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
