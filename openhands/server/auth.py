import jwt
from fastapi import Request
from jwt.exceptions import InvalidTokenError
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger


def get_github_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'github_token', None)


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'github_user_id', None)
