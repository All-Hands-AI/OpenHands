from abc import ABC, abstractmethod
from typing import Callable

from openhands.app_server.user.user_service import UserService
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class UserAdminService(ABC):
    """Service for user administration"""

    @abstractmethod
    async def get_user_service(self, user_id: str) -> UserService | None:
        """Get a user service for this id given."""


class UserAdminServiceManager(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_unsecured_resolver(self) -> Callable:
        """Get a resolver for instances of user admin service ."""
