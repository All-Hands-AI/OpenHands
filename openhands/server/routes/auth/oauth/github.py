from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
import httpx
import os
from database.db import db
from database.models.user import User
from database.models.provider_token import ProviderToken, ProviderType

router = APIRouter()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("FRONTEND_URL", "https://openhands.fly.dev") + "/auth/callback/github"

@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth login"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
    auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:email"
    return RedirectResponse(auth_url)

@router.get("/callback/github")
async def github_callback(code: str, request: Request):
    """Handle GitHub OAuth callback"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
    # Exchange code for token
    token_url = "https://github.com/login/oauth/access_token"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI
            },
            headers={"Accept": "application/json"}
        )
        
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get GitHub token")
        
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # Get user info from GitHub
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
    
    if user_response.status_code != 200 or email_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get GitHub user info")
        
    user_data = user_response.json()
    emails = email_response.json()
    
    # Get primary email
    primary_email = next((email["email"] for email in emails if email["primary"]), None)
    if not primary_email:
        primary_email = emails[0]["email"] if emails else None
        
    if not primary_email:
        raise HTTPException(status_code=400, detail="No email found in GitHub account")
        
    # Check if user exists with this email
    existing_user = await db.fetchrow("SELECT * FROM users WHERE email = $1", primary_email)
    
    if existing_user:
        # User exists, check if GitHub provider token exists
        user_id = existing_user["id"]
        provider_token = await db.fetchrow(
            "SELECT * FROM provider_tokens WHERE user_id = $1 AND provider_type = $2",
            user_id, ProviderType.GITHUB.value
        )
        
        if not provider_token:
            # Create provider token
            await db.execute(
                """
                INSERT INTO provider_tokens 
                (user_id, provider_type, provider_user_id, access_token)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, ProviderType.GITHUB.value, str(user_data["id"]), access_token
            )
    else:
        # Create new user
        username = user_data.get("login") or f"github_{user_data['id']}"
        
        # Generate a random password for the user
        import secrets
        import string
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
        password_hash = User.hash_password(password)
        
        # Create user
        user_id = await db.fetchval(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            username, primary_email, password_hash
        )
        
        # Create provider token
        await db.execute(
            """
            INSERT INTO provider_tokens 
            (user_id, provider_type, provider_user_id, access_token)
            VALUES ($1, $2, $3, $4)
            """,
            user_id, ProviderType.GITHUB.value, str(user_data["id"]), access_token
        )
    
    # Create user object and generate JWT
    if existing_user:
        user = User(
            id=user_id,
            username=existing_user["username"],
            email=primary_email,
            password_hash=existing_user["password_hash"],
            created_at=existing_user["created_at"],
            updated_at=existing_user["updated_at"]
        )
    else:
        # For new users, we already have the values in local variables
        from datetime import datetime
        now = datetime.utcnow()
        user = User(
            id=user_id,
            username=username,
            email=primary_email,
            password_hash=password_hash,
            created_at=now,
            updated_at=now
        )
    
    # Generate JWT token
    token = user.generate_token()
    
    # Redirect to frontend with token
    frontend_url = os.getenv("FRONTEND_URL", "https://openhands.fly.dev")
    redirect_url = f"{frontend_url}/auth/oauth-callback?token={token}"
    
    return RedirectResponse(redirect_url)
