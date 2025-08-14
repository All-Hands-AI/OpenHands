from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server import shared
from openhands.server.settings import Settings
from openhands.server.user_auth.user_auth import AuthType, UserAuth
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.file_secrets_store import FileSecretsStore
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.storage.settings.settings_store import SettingsStore


SESSION_COOKIE_NAME = "oh_session"
JWT_ALG = "HS256"


@dataclass
class GithubCookieUserAuth(UserAuth):
    """Cookie/JWT-based user authentication for GitHub SSO.

    - Reads a signed JWT from an HTTP-only cookie to identify the user
    - Provides per-user settings and secrets stores under users/{user_id}/...
    - Returns provider tokens loaded from the per-user secrets store
    """

    request: Request

    _user_id: str | None = None
    _user_email: str | None = None
    _claims: dict[str, Any] = field(default_factory=dict)

    _settings: Settings | None = None
    _settings_store: SettingsStore | None = None
    _secrets_store: SecretsStore | None = None
    _user_secrets: UserSecrets | None = None

    def _load_from_cookie(self) -> None:
        token = self.request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return
        secret = shared.config.jwt_secret.get_secret_value() if shared.config.jwt_secret else None
        if not secret:
            return
        try:
            claims = jwt.decode(token, secret, algorithms=[JWT_ALG])
            # required user id
            sub = claims.get("sub")
            if sub:
                self._user_id = str(sub)
            self._user_email = claims.get("email")
            self._claims = claims
        except Exception:
            # Invalid/expired token -> treated as anonymous
            self._user_id = None
            self._user_email = None
            self._claims = {}

    def get_auth_type(self) -> AuthType | None:
        return AuthType.COOKIE

    async def get_user_id(self) -> str | None:
        if self._user_id is None:
            self._load_from_cookie()
        return self._user_id

    async def get_user_email(self) -> str | None:
        if self._user_id is None:
            self._load_from_cookie()
        return self._user_email

    async def get_access_token(self) -> SecretStr | None:
        # Access tokens should be retrieved from provider tokens stored in secrets
        return None

    def _get_user_scoped_settings_path(self, user_id: str | None) -> str:
        safe_id = user_id or "anonymous"
        return f"users/{safe_id}/settings.json"

    def _get_user_scoped_secrets_path(self, user_id: str | None) -> str:
        safe_id = user_id or "anonymous"
        return f"users/{safe_id}/secrets.json"

    async def get_user_settings_store(self) -> SettingsStore:
        store = self._settings_store
        if store:
            return store
        user_id = await self.get_user_id()
        file_store = get_file_store(
            shared.config.file_store,
            shared.config.file_store_path,
            shared.config.file_store_web_hook_url,
            shared.config.file_store_web_hook_headers,
        )
        self._settings_store = FileSettingsStore(
            file_store=file_store,
            path=self._get_user_scoped_settings_path(user_id),
        )
        return self._settings_store

    async def get_secrets_store(self) -> SecretsStore:
        store = self._secrets_store
        if store:
            return store
        user_id = await self.get_user_id()
        file_store = get_file_store(
            shared.config.file_store,
            shared.config.file_store_path,
            shared.config.file_store_web_hook_url,
            shared.config.file_store_web_hook_headers,
        )
        self._secrets_store = FileSecretsStore(
            file_store=file_store,
            path=self._get_user_scoped_secrets_path(user_id),
        )
        return self._secrets_store

    async def get_user_secrets(self) -> UserSecrets | None:
        secrets = self._user_secrets
        if secrets:
            return secrets
        secrets_store = await self.get_secrets_store()
        self._user_secrets = await secrets_store.load()
        return self._user_secrets

    async def get_provider_tokens(self) -> PROVIDER_TOKEN_TYPE | None:
        user_secrets = await self.get_user_secrets()
        if not user_secrets:
            return None
        return user_secrets.provider_tokens

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        # Instance is per-request, reads cookie lazily
        return GithubCookieUserAuth(request=request)

    @staticmethod
    def issue_session_cookie(sub: str, email: str | None = None, login: str | None = None, name: str | None = None, avatar_url: str | None = None, expires_in_hours: int = 720) -> tuple[str, int]:
        """Utility to create a JWT suitable for setting in a cookie.
        Returns (token, max_age_seconds).
        """
        secret = shared.config.jwt_secret.get_secret_value() if shared.config.jwt_secret else None
        if not secret:
            raise ValueError("Missing JWT secret")
        now = datetime.now(tz=timezone.utc)
        exp = now + timedelta(hours=expires_in_hours)
        payload: dict[str, Any] = {
            "sub": str(sub),
            "email": email,
            "login": login,
            "name": name,
            "avatar_url": avatar_url,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(payload, secret, algorithm=JWT_ALG)
        return token, int((exp - now).total_seconds())