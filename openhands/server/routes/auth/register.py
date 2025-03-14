from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, SecretStr, validator

from database.models.user import User, UserCreate, UserResponse
from database.db import db

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr
    confirm_password: SecretStr
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v.get_secret_value() != values['password'].get_secret_value():
            raise ValueError('Passwords do not match')
        return v

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest):
    # Check if email already exists
    existing_email = await db.fetchval(
        "SELECT id FROM users WHERE email = $1", 
        user_data.email
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await db.fetchval(
        "SELECT id FROM users WHERE username = $1", 
        user_data.username
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Hash password
    password_hash = User.hash_password(user_data.password.get_secret_value())
    
    # Insert new user
    user_id = await db.fetchval(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        user_data.username,
        user_data.email,
        password_hash
    )
    
    # Get created user
    user_data = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        user_id
    )
    
    # Create user object
    user = User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        password_hash=user_data["password_hash"],
        created_at=user_data["created_at"],
        updated_at=user_data["updated_at"]
    )
    
    return user.to_response()
