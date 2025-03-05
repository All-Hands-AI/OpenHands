from fastapi import Request
from pydantic import SecretStr

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE


def get_provider_tokens(request: Request) -> PROVIDER_TOKEN_TYPE | None:
    """Get GitHub token from request state. For backward compatibility."""
    return getattr(request.state, 'provider_tokens', {})


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)


def get_idp_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'idp_token', None)
