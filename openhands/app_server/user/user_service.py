from abc import ABC, abstractmethod
from typing import Callable

from openhands.app_server.user.user_models import (
    UserInfo,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class UserService(ABC):
    """Service for managing users."""

    # Read methods

    @abstractmethod
    async def get_current_user(self) -> UserInfo:
        """Get the current user"""


class UserServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_resolver_for_user(self) -> Callable:
        """Get a resolver which may be used to resolve an instance of user service
        limited to the current user.
        """
