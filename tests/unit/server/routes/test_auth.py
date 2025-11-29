from fastapi import APIRouter, Depends
from openhands.server.user_auth import get_user_auth
from openhands.server.user_auth.user_auth import UserAuth

router = APIRouter()

@router.get("/test-auth")
async def test_auth_endpoint(user_auth: UserAuth = Depends(get_user_auth)):
    """Verify authentication details of the current user."""
    return {
        "user_id": await user_auth.get_user_id(),
        "email": await user_auth.get_user_email(),
        "auth_type": user_auth.get_auth_type().value if user_auth.get_auth_type() else None,
        "has_token": (await user_auth.get_access_token()) is not None,
    }
