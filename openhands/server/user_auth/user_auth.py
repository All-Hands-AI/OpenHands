from __future__ import annotations
from abc import ABC, abstractmethod
import os
from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server.settings import Settings
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl


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
        """ Get the settings store for the current user."""

    async def get_user_settings(self) -> Settings | None:
        """ Get the user settings for the current user"""
        settings = self._settings
        if settings:
            return settings
        settings_store = await self.get_user_settings_store()
        settings = await settings_store.load()  
        self._settings = settings   
        return settings   

    @classmethod
    @abstractmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        """Get an instance of UserAuth from the request given"""


async def get_user_auth(request: Request) -> UserAuth:
    impl_name = os.environ.get('USER_AUTH_CLASS') or UserAuth.__class__.__qualname__
    impl: UserAuth = get_impl(UserAuth, impl_name)
    result = await impl.get_instance(request)
    return result
