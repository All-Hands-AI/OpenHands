from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.integrations.service_types import ProviderType
from openhands.server.settings import Settings
from openhands.server.user_auth.user_auth import AuthType, get_user_auth
from openhands.storage.settings.settings_store import SettingsStore


async def get_provider_tokens(request: Request) -> PROVIDER_TOKEN_TYPE | None:
    user_auth = await get_user_auth(request)
    provider_tokens = await user_auth.get_provider_tokens()
    return provider_tokens


async def get_access_token(request: Request) -> SecretStr | None:
    user_auth = await get_user_auth(request)
    access_token = await user_auth.get_access_token()
    return access_token


async def get_user_id(request: Request) -> str | None:
    user_auth = await get_user_auth(request)
    user_id = await user_auth.get_user_id()
    return user_id


async def get_github_user_id(request: Request) -> str | None:
    provider_tokens = await get_provider_tokens(request)
    if not provider_tokens:
        return None
    github_provider = provider_tokens.get(ProviderType.GITHUB)
    if github_provider:
        return github_provider.user_id
    return None


async def get_user_settings(request: Request) -> Settings | None:
    user_auth = await get_user_auth(request)
    user_settings = await user_auth.get_user_settings()
    return user_settings


async def get_user_settings_store(request: Request) -> SettingsStore | None:
    user_auth = await get_user_auth(request)
    user_settings_store = await user_auth.get_user_settings_store()
    return user_settings_store


async def get_auth_type(request: Request) -> AuthType | None:
    user_auth = await get_user_auth(request)
    return user_auth.get_auth_type()