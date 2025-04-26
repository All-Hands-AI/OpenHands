from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.thesis_auth import add_invite_code_to_user

app = APIRouter(prefix='/api/invitation')


class InvitationCode(BaseModel):
    code: str


@app.post('/validate', response_model=dict)
async def validate_invitation_code(
    invitation: InvitationCode, request: Request
) -> dict:
    """Validate an invitation code and update user status.

    This endpoint validates an invitation code and if valid:
    1. Updates the user's status to 'activated'
    2. Marks the invitation code as used

    A user can only validate one invitation code.
    """
    try:
        # The middleware already checked whitelist status
        await add_invite_code_to_user(
            invitation.code,
            request.headers.get('Authorization'),
            request.headers.get('x-device-id'),
        )
        return {'valid': True, 'reason': 'Invitation code activated successfully'}
    except Exception as e:
        logger.error(f'Error validating invitation code: {e}')
        raise HTTPException(
            status_code=400,
            detail=str(e.detail) if hasattr(e, 'detail') else str(e),
        )
