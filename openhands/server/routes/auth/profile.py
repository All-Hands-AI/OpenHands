from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from database.models.user import User, UserResponse
from database.db import db
from openhands.server.routes.auth.login import oauth2_scheme

router = APIRouter()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = User.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    user_data = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1", 
        user_id
    )
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        password_hash=user_data["password_hash"],
        created_at=user_data["created_at"],
        updated_at=user_data["updated_at"]
    )

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user.to_response()

class UpdateProfileRequest(BaseModel):
    username: str = None
    email: EmailStr = None

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user)
):
    # Check if username is being updated and is not already taken
    if profile_data.username and profile_data.username != current_user.username:
        existing_username = await db.fetchval(
            "SELECT id FROM users WHERE username = $1 AND id != $2", 
            profile_data.username,
            current_user.id
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if email is being updated and is not already registered
    if profile_data.email and profile_data.email != current_user.email:
        existing_email = await db.fetchval(
            "SELECT id FROM users WHERE email = $1 AND id != $2", 
            profile_data.email,
            current_user.id
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user data
    updates = {}
    if profile_data.username:
        updates["username"] = profile_data.username
    if profile_data.email:
        updates["email"] = profile_data.email
    
    if updates:
        set_clause = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(updates.keys())])
        values = list(updates.values())
        
        await db.execute(
            f"UPDATE users SET {set_clause}, updated_at = NOW() WHERE id = $1",
            current_user.id,
            *values
        )
    
    # Get updated user
    user_data = await db.fetchrow(
        "SELECT * FROM users WHERE id = $1",
        current_user.id
    )
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        password_hash=user_data["password_hash"],
        created_at=user_data["created_at"],
        updated_at=user_data["updated_at"]
    ).to_response()
