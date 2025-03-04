from typing import Literal

from fastapi import Request
from pydantic import SecretStr


def get_github_token(request: Request) -> SecretStr | None:
    """Get GitHub token from request state. For backward compatibility."""
    return getattr(request.state, 'github_token', None)


def get_gitlab_token(request: Request) -> SecretStr | None:
    """Get GitHub token from request state. For backward compatibility."""
    return getattr(request.state, 'gitlab_token', None)


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)


def get_idp_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'idp_token', None)
