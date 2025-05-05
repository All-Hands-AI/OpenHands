from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server.settings import Settings
from openhands.server.shared import server_config
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl


class AuthType(Enum):
    COOKIE = 'cookie'
    BEARER = 'bearer'


class UserAuth(ABC):
    """Extensible class encapsulating user Authentication"""

    _settings: Settings | None

    @abstractmethod
    async def get_user_id(self) -> str | None:
        """Get the unique identifier for the current user"""

    @abstractmethod
    async def get_access_token(self) -> SecretStr | None:
        """Get the access token for the current user"""

    @abstractmethod
    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        """Get the provider tokens for the current user."""

    @abstractmethod
    async def get_user_settings_store(self) -> SettingsStore | None:
        """Get the settings store for the current user."""

    async def get_user_settings(self) -> Settings | None:
        """Get the user settings for the current user"""
        settings = self._settings
        if settings:
            return settings
        settings_store = await self.get_user_settings_store()
        if settings_store is None:
            return None
        settings = await settings_store.load()
        self._settings = settings
        return settings

    @abstractmethod
    async def get_secrets_store(self) -> SecretsStore:
        """Get secrets store"""

    @abstractmethod
    async def get_user_secrets(self) -> UserSecrets | None:
        """Get the user's secrets"""

    def get_auth_type(self) -> AuthType | None:
        return None

    @classmethod
    @abstractmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        """Get an instance of UserAuth from the request given"""


async def get_user_auth(request: Request) -> UserAuth:
    user_auth = getattr(request.state, 'user_auth', None)
    if user_auth:
        return user_auth
    impl_name = server_config.user_auth_class
    impl = get_impl(UserAuth, impl_name)
    user_auth = await impl.get_instance(request)
    request.state.user_auth = user_auth
    return user_auth
