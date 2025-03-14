from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from pydantic import BaseModel, EmailStr, SecretStr, Field
import bcrypt

# Configuration (should be moved to settings)
JWT_SECRET = "your-secret-key"  # This should be in environment variables
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(days=1)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr

class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

class User:
    """User model with authentication methods"""
    
    def __init__(self, id: int, username: str, email: str, password_hash: str, 
                 created_at: datetime, updated_at: datetime):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a stored password against one provided by user"""
        return bcrypt.checkpw(password.encode('utf-8'), 
                             self.password_hash.encode('utf-8'))
    
    def generate_token(self) -> str:
        """Generate JWT token for the user"""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify a JWT token and return payload if valid"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    def to_response(self) -> UserResponse:
        """Convert to response model"""
        return UserResponse(
            id=self.id,
            username=self.username,
            email=self.email,
            created_at=self.created_at
        )
