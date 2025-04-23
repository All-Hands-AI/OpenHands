

from fastapi import Request
from pydantic import SecretStr
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.integrations.service_types import ProviderType
from openhands.server.user_auth.user_auth import get_user_auth


async def get_provider_tokens(request: Request) -> PROVIDER_TOKEN_TYPE:
    user_auth = await get_user_auth(request)
    provider_tokens = await user_auth.get_provider_tokens()
    return provider_tokens


async def get_access_token(request: Request) -> SecretStr:
    user_auth = await get_user_auth(request)
    access_token = await user_auth.get_access_token()
    return access_token


async def get_user_id(request: Request) -> str:
    user_auth = await get_user_auth(request)
    user_id = await user_auth.get_user_id()
    return user_id


async def get_github_user_id(request: Request) -> str | None:
    provider_tokens = await get_provider_tokens(request)
    if provider_tokens and ProviderType.GITHUB in provider_tokens:
        return provider_tokens[ProviderType.GITHUB].user_id

    return None
