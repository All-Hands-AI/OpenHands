from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from openhands.app_server.user.user_models import (
    UserInfo,
)
from openhands.integrations.provider import ProviderType
from openhands.sdk.conversation.secret_source import SecretSource
from openhands.sdk.utils.models import DiscriminatedUnionMixin


class UserContext(ABC):
    """Service for managing users."""

    # Read methods

    @abstractmethod
    async def get_user_id(self) -> str | None:
        """Get the user id"""

    @abstractmethod
    async def get_user_info(self) -> UserInfo:
        """Get the user info."""

    @abstractmethod
    async def get_authenticated_git_url(self, repository: str) -> str:
        """Get the provider tokens for the user"""

    @abstractmethod
    async def get_latest_token(self, provider_type: ProviderType) -> str | None:
        """Get the latest token for the provider type given"""

    @abstractmethod
    async def get_secrets(self) -> dict[str, SecretSource]:
        """Get custom secrets and github provider secrets for the conversation."""


class UserContextInjector(DiscriminatedUnionMixin, ABC):
    @abstractmethod
    def get_injector(self) -> Callable[..., UserContext | Awaitable[UserContext]]:
        """Get a resolver for instances of user service limited to the current user. Caches the user context
        in the current request as the `user_context` attribute"""

    @abstractmethod
    async def get_for_user(self, user_id: str | None) -> UserContext:
        """Get a user context for the user with the id given."""
