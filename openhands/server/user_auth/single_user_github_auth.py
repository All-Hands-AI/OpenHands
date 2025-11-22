from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from pydantic import SecretStr

from openhands.server import shared
from openhands.server.settings import Settings
from openhands.server.user_auth.user_auth import AuthType, UserAuth
from openhands.storage.data_models.secrets import Secrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.settings_store import SettingsStore


@dataclass
class SingleUserGithubAuth(UserAuth):
    """Authentication class for single-user GitHub access using cookies."""

    user_id: str | None
    access_token: SecretStr | None
    auth_type: AuthType = AuthType.COOKIE
    _settings: Settings | None = None
    _settings_store: SettingsStore | None = None
    _secrets_store: SecretsStore | None = None

    async def get_user_id(self) -> str | None:
        return self.user_id

    async def get_user_email(self) -> str | None:
        return None

    async def get_access_token(self) -> SecretStr | None:
        return self.access_token

    def get_auth_type(self) -> AuthType | None:
        return self.auth_type

    async def get_provider_tokens(self):
        return None

    async def get_secrets(self) -> Secrets | None:
        return None

    async def _get_cached_store(
        self, store_attr: str, store_impl, error_msg: str
    ):
        """Helper to get cached store instance."""
        cached = getattr(self, store_attr, None)
        if cached:
            return cached

        store = await store_impl.get_instance(shared.config, self.user_id)
        if store is None:
            raise ValueError(error_msg)

        setattr(self, store_attr, store)
        return store

    async def get_user_settings_store(self) -> SettingsStore:
        return await self._get_cached_store(
            '_settings_store',
            shared.SettingsStoreImpl,
            'Failed to get settings store instance',
        )

    async def get_secrets_store(self) -> SecretsStore:
        return await self._get_cached_store(
            '_secrets_store',
            shared.SecretsStoreImpl,
            'Failed to get secrets store instance',
        )

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        """Extracts credentials from request cookies"""
        user_id = request.cookies.get('github_user_id')
        token_str = request.cookies.get('github_token')

        access_token = SecretStr(token_str) if token_str else None

        return cls(user_id=user_id, access_token=access_token)

    @classmethod
    async def get_for_user(cls, user_id: str) -> UserAuth:
        """Creates an auth instance for a given user ID without a token."""
        return cls(user_id=user_id, access_token=None)
