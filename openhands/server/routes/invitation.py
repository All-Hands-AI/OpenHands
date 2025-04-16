from fastapi import APIRouter, Request
from openhands.server.auth import get_user_id
from openhands.server.thesis_auth import add_invite_code_to_user
from openhands.core.logger import openhands_logger as logger

app = APIRouter(prefix='/api/invitation')


@app.post("/validate/{code}", response_model=dict)
async def validate_invitation_code(code: str, request: Request) -> dict:
    """Validate an invitation code and update user status.

    This endpoint validates an invitation code and if valid:
    1. Updates the user's status to 'activated'
    2. Marks the invitation code as used

    A user can only validate one invitation code.
    """
    user_id = get_user_id(request)
    # The middleware already checked whitelist status
    add_invite_code_to_user(code, request.headers.get("Authorization"))
    return {
        "valid": True,
        "reason": "Invitation code activated successfully"
    }
