import secrets
import string
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, update, delete

from openhands.server.auth import get_user_id
from openhands.server.db import database
from openhands.server.models import InvitationCode, User
from openhands.core.logger import openhands_logger as logger

app = APIRouter(prefix='/api/invitation')

# Constants
ADMIN_INVITATION_CODE = "0xc4dde52e318ccc67596c20a09e4c29ce369d8e51"  # Whitelisted admin address
CODE_LENGTH = 10  # Length of generated invitation codes
MAX_CODES_PER_REQUEST = 100  # Maximum number of codes that can be generated in one request


class InvitationCodeCreate(BaseModel):
    limit: int = Field(default=1, ge=1, le=MAX_CODES_PER_REQUEST, description="Number of invitation codes to generate")


class InvitationCodeResponse(BaseModel):
    code: str
    created_by: str
    created_at: datetime
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None


async def check_admin_access(request: Request) -> str:
    """Check if the user has admin access for invitation code management."""
    user_id = get_user_id(request)

    # Only allow whitelisted address
    if user_id.lower() == ADMIN_INVITATION_CODE.lower():
        return user_id
    
    # Reject all other users
    raise HTTPException(status_code=403, detail="Access denied.")


def generate_invitation_code() -> str:
    """Generate a random invitation code."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(CODE_LENGTH))


@app.post("/", response_model=List[InvitationCodeResponse])
async def create_invitation_code(
    request: Request,
    invitation: InvitationCodeCreate = None
) -> List[InvitationCodeResponse]:
    """Create one or more invitation codes.
    
    Args:
        limit: Number of invitation codes to generate (max 100)
    """
    user_id = await check_admin_access(request)
    
    # Default to 1 if not specified
    limit = 1
    if invitation and invitation.limit:
        limit = min(invitation.limit, MAX_CODES_PER_REQUEST)
    
    created_codes = []
    
    for _ in range(limit):
        # Generate a unique code
        while True:
            code = generate_invitation_code()
            # Check if code already exists
            query = select(InvitationCode).where(InvitationCode.c.code == code)
            existing_code = await database.fetch_one(query)
            if not existing_code:
                break
        
        # Create new invitation code
        invitation_data = {
            "code": code,
            "created_by": user_id.lower(),
        }
        
        await database.execute(InvitationCode.insert().values(invitation_data))
        
        # Fetch the created invitation
        query = select(InvitationCode).where(InvitationCode.c.code == code)
        created_invitation = await database.fetch_one(query)
        created_codes.append(InvitationCodeResponse(**created_invitation))
    
    return created_codes


@app.get("/", response_model=List[InvitationCodeResponse])
async def list_invitation_codes(request: Request) -> List[InvitationCodeResponse]:
    """List all invitation codes created by the user."""
    user_id = await check_admin_access(request)

    logger.info(f"Listing invitation codes for user: {user_id}")
    
    # Whitelisted admin can see all codes
    if user_id.lower() == ADMIN_INVITATION_CODE.lower():
        query = select(InvitationCode).order_by(InvitationCode.c.created_at.desc())
    else:
        # Regular users can only see their own codes
        query = select(InvitationCode).where(
            InvitationCode.c.created_by == user_id.lower()
        ).order_by(InvitationCode.c.created_at.desc())
    
    invitation_codes = await database.fetch_all(query)
    return [InvitationCodeResponse(**code) for code in invitation_codes]


@app.delete("/{code}", response_model=dict)
async def delete_invitation_code(code: str, request: Request) -> dict:
    """Delete an invitation code."""
    user_id = await check_admin_access(request)
    
    # Get the existing code
    query = select(InvitationCode).where(InvitationCode.c.code == code)
    invitation_code = await database.fetch_one(query)
    
    if not invitation_code:
        raise HTTPException(status_code=404, detail="Invitation code not found")
    
    # Only the creator or whitelisted admin can delete code
    if (user_id.lower() != invitation_code["created_by"].lower() and 
        user_id.lower() != ADMIN_INVITATION_CODE.lower()):
        raise HTTPException(status_code=403, detail="Not authorized to delete this code")
    
    # Check if code is already used
    if invitation_code["used_by"]:
        raise HTTPException(status_code=400, detail="Cannot delete a used invitation code")
    
    # Delete the code
    await database.execute(
        delete(InvitationCode).where(InvitationCode.c.code == code)
    )
    
    return {"success": True, "message": "Invitation code deleted successfully"}


@app.post("/validate/{code}", response_model=dict)
async def validate_invitation_code(code: str, request: Request) -> dict:
    """Validate an invitation code and update user status.
    
    This endpoint validates an invitation code and if valid:
    1. Updates the user's status to 'activated'
    2. Marks the invitation code as used
    
    A user can only validate one invitation code.
    """
    user_id = get_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if user has already been activated or used an invitation code
    user_query = select(User).where(User.c.public_key == user_id.lower())
    user = await database.fetch_one(user_query)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["status"] == "activated":
        return {"valid": False, "reason": "User is already activated"}
    
    # Get the existing code
    query = select(InvitationCode).where(InvitationCode.c.code == code)
    invitation_code = await database.fetch_one(query)
    
    if not invitation_code:
        raise HTTPException(status_code=404, detail="Invitation code not found")
    
    # Check if code is already used
    if invitation_code["used_by"]:
        return {"valid": False, "reason": "Invitation code has already been used"}
    
    # If the code is valid, update user status and mark code as used
    try:
        # Mark the code as used
        await database.execute(
            update(InvitationCode)
            .where(InvitationCode.c.code == code)
            .values({
                "used_by": user_id.lower(),
                "used_at": datetime.now()
            })
        )
        
        # Update user status to activated
        await database.execute(
            update(User)
            .where(User.c.public_key == user_id.lower())
            .values({"status": "activated"})
        )
        
        logger.info(f"User {user_id} activated with invitation code {code}")
        
        return {
            "valid": True, 
            "status": "activated",
            "message": "User has been activated successfully"
        }
    except Exception as e:
        logger.error(f"Error activating user {user_id} with code {code}: {str(e)}")
        # If there's an error during the update, return an error
        return {
            "valid": False,
            "reason": f"Error activating user: {str(e)}"
        } 