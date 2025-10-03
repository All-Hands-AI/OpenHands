


from typing import Callable

from openhands.app_server.user.legacy_user_service import LegacyUserService
from openhands.app_server.user.user_admin_service import UserAdminService, UserAdminServiceResolver
from openhands.app_server.user.user_service import UserService
from openhands.server.user_auth.user_auth import get_for_user


class LegacyUserAdminService(UserAdminService):

    async def get_user_service(self, user_id: str) -> UserService | None:
        """ Get a user service for this id given."""
        user_auth = await get_for_user(user_id)
        return LegacyUserService(
            user_auth=user_auth
        )


class LegacyUserAdminServiceResolver(UserAdminServiceResolver):

    def get_unsecured_resolver(self) -> Callable:
        return LegacyUserAdminService
