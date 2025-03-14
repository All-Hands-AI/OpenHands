from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from database.db import db
from openhands.server.routes.auth.profile import get_current_user
from database.models.user import User

router = APIRouter()

class UserSettings(BaseModel):
    settings_json: dict

@router.get("/settings")
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get user settings from database"""
    settings = await db.fetchrow(
        "SELECT settings_json FROM user_settings WHERE user_id = $1",
        current_user.id
    )
    
    if not settings:
        # Return empty settings if not found
        return {"settings_json": {}}
    
    return {"settings_json": settings["settings_json"]}

@router.put("/settings")
async def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user)
):
    """Update user settings in database"""
    # Check if settings exist for user
    existing = await db.fetchval(
        "SELECT id FROM user_settings WHERE user_id = $1",
        current_user.id
    )
    
    if existing:
        # Update existing settings
        await db.execute(
            """
            UPDATE user_settings 
            SET settings_json = $1, updated_at = NOW()
            WHERE user_id = $2
            """,
            settings.settings_json,
            current_user.id
        )
    else:
        # Insert new settings
        await db.execute(
            """
            INSERT INTO user_settings (user_id, settings_json)
            VALUES ($1, $2)
            """,
            current_user.id,
            settings.settings_json
        )
    
    return {"status": "success"}
