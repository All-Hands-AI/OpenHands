"""User router for OpenHands Server. For the moment, this simply implements the /me endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from openhands.app_server.dependency import get_dependency_resolver
from openhands.app_server.user.user_models import UserInfo
from openhands.app_server.user.user_service import UserService

router = APIRouter(prefix='/users', tags=['User'])
user_service_dependency = Depends(
    get_dependency_resolver().user.get_resolver_for_user()
)

# Read methods


@router.get('/me')
async def get_current_user(
    user_service: UserService = user_service_dependency,
) -> UserInfo:
    """Get the current authenticated user."""
    user = await user_service.get_current_user()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    return user
