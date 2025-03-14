from datetime import datetime
import uuid
from typing import Optional

class Session:
    """Session model for managing user sessions"""
    
    def __init__(self, id: int, user_id: int, token: str, 
                 expires_at: datetime, created_at: datetime, updated_at: datetime):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def generate_token() -> str:
        """Generate a unique session token"""
        return str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        """Check if the session is expired"""
        return datetime.utcnow() > self.expires_at
