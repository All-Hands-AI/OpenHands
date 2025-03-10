from fastapi import Request
from pydantic import SecretStr


def get_access_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'access_token', None)


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'user_id', None)


def get_github_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'github_token', None)


def get_github_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)
