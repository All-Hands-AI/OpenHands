"""User router for OpenHands Server. For the moment, this simply implements the /me endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from openhands.app_server.config import user_manager
from openhands.app_server.user.user_models import UserInfo
from openhands.app_server.user.user_service import UserService

router = APIRouter(prefix='/users', tags=['User'])
user_service_dependency = Depends(
    user_manager().get_resolver_for_current_user()
)

# Read methods


@router.get('/me')
async def get_current_user(
    user_service: UserService = user_service_dependency,
) -> UserInfo:
    """Get the current authenticated user."""
    user = await user_service.get_user_info()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    return user
