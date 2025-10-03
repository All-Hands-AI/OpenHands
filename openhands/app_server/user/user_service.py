from abc import ABC, abstractmethod
from typing import Callable

from openhands.app_server.user.user_models import (
    UserInfo,
)
from openhands.sdk.utils.models import DiscriminatedUnionMixin

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, ProviderHandler, ProviderType


class UserService(ABC):
    """Service for managing users."""

    # Read methods

    @abstractmethod
    async def get_user_id(self) -> str:
        """Get the user id"""

    @abstractmethod
    async def get_user_info(self) -> UserInfo:
        """Get the user info."""

    @abstractmethod
    async def get_authenticated_git_url(self, repository: str) -> str:
        """Get the provider tokens for the user"""

    @abstractmethod
    async def get_latest_token(self, provider_type: ProviderType) -> str | None:
        """ Get the latest token for the provider type given"""


class UserServiceResolver(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_resolver_for_current_user(self) -> Callable:
        """Get a resolver for instances of user service limited to the current user."""
