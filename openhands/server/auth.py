from typing import Literal

from fastapi import Request
from pydantic import SecretStr


def get_token(request: Request) -> SecretStr | None:
    """Get the token from request state."""
    return getattr(request.state, 'token', None)


def get_token_type(request: Request) -> Literal['github', 'gitlab'] | None:
    """Get the token type from request state."""
    return getattr(request.state, 'token_type', None)


def get_github_token(request: Request) -> SecretStr | None:
    """Get GitHub token from request state. For backward compatibility."""
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type == 'github':
        return token
    return getattr(request.state, 'github_token', None)


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)


def get_idp_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'idp_token', None)
