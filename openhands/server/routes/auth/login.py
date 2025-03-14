from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from database.models.user import User, UserLogin
from database.db import db

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user by email
    user_data = await db.fetchrow(
        "SELECT * FROM users WHERE email = $1", 
        form_data.username  # OAuth2PasswordRequestForm uses username field for email
    )
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
    
    # Verify password
    if not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = user.generate_token()
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    payload = User.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"valid": True, "user_id": payload.get("user_id")}
