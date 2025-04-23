
from dataclasses import dataclass
from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, SecretStore
from openhands.integrations.service_types import ProviderType
from openhands.server import shared
from openhands.server.user_auth.user_auth import UserAuth
from openhands.server.settings import Settings
from openhands.storage.settings.settings_store import SettingsStore


@dataclass
class DefaultUserAuth(UserAuth):
    """Default user authentication mechanism"""
    _settings: Settings | None = None

    async def get_user_id(self) -> str | None:
        """The default implementation does not support multi tenancy, so user_id is always None """
        return None

    async def get_access_token(self) -> SecretStr:
        """The default implementation does not support multi tenancy, so access_token is always None """
        return None
    
    async def _get_settings(self) -> Settings | None:
        settings = self._settings
        if settings:
            return settings
        user_id = await self.get_user_id()
        settings_store: SettingsStore = await shared.SettingsStoreImpl.get_instance(
            shared.config, user_id
        )
        settings = await settings_store.load()  
        self._settings = settings   
        return settings   

    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE:
        settings = await self._get_settings()
        secrets_store: SecretStore = getattr(settings, 'secrets_store', None)
        provider_tokens = getattr(secrets_store, 'provider_tokens', None) or {}
        return provider_tokens

    @classmethod
    def get_instance(cls, request: Request) -> UserAuth:
        user_auth = getattr(request.state, 'user_auth', None)
        if user_auth:
            return user_auth
        user_auth = DefaultUserAuth()
        request.state.user_auth = user_auth
        return user_auth
