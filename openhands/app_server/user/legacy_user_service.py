
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends
from openhands.app_server.user.user_models import UserInfo
from openhands.app_server.user.user_service import UserService, UserServiceResolver
from openhands.server.user_auth import get_user_id, get_user_settings
from openhands.storage.data_models.settings import Settings

# In legacy mode for OSS, there is only a single unconstrained user
DEFAULT_USER = "root"


@dataclass
class LegacyUserService(UserService):
    """Interface to old user settings service."""
    user_id: str
    settings: Settings

    async def get_current_user(self) -> UserInfo:
        return UserInfo(
            id=self.user_id,
            **self.settings.model_dump()
        )


class LegacyUserServiceResolver(UserServiceResolver):

    def get_resolver_for_user(self) -> Callable:
        return self._resolve_for_user

    def _resolve_for_user(
        self,
        user_id: str | None = Depends(get_user_id),
        settings: Settings = Depends(get_user_settings),
    ) -> UserService:
        if user_id is None and settings:
            user_id = DEFAULT_USER
        return LegacyUserService(user_id, settings)
