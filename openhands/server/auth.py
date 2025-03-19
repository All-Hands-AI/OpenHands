import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import PROVIDER_TOKEN_TYPE, ProviderType
from openhands.server.shared import config


def get_provider_tokens(request: Request) -> PROVIDER_TOKEN_TYPE | None:
    """Get GitHub token from request state. For backward compatibility."""
    return getattr(request.state, 'provider_tokens', None)


def get_access_token(request: Request) -> SecretStr | None:
    return getattr(request.state, 'access_token', None)


def get_user_id(request: Request) -> str | None:
    return getattr(request.state, 'user_id', None)


def get_github_token(request: Request) -> SecretStr | None:
    provider_tokens = get_provider_tokens(request)

    if provider_tokens and ProviderType.GITHUB in provider_tokens:
        return provider_tokens[ProviderType.GITHUB].token

    return None


def get_github_user_id(request: Request) -> str | None:
    provider_tokens = get_provider_tokens(request)
    if provider_tokens and ProviderType.GITHUB in provider_tokens:
        return provider_tokens[ProviderType.GITHUB].user_id

    return None


api_key_header = APIKeyHeader(name='Authorization', auto_error=True)


def verify_token_api(auth_header: str = Depends(api_key_header)):
    try:
        verify_token(auth_header)
    except (
        jwt.ExpiredSignatureError,
        jwt.MissingRequiredClaimError,
        jwt.InvalidTokenError,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid authentication token',
        )


def verify_token(auth_header: str):
    logger.debug('verify_token start')
    if not config.jwt_secret_client_auth:
        raise RuntimeError('JWT secret not found')
    jwt_secret_client_auth = (
        config.jwt_secret_client_auth.get_secret_value()
        if isinstance(config.jwt_secret_client_auth, SecretStr)
        else config.jwt_secret_client_auth
    )
    decoded = jwt.decode(
        auth_header[7:],
        jwt_secret_client_auth,
        options={'require': ['user_id']},
        algorithms=['HS256'],
    )
    logger.debug(f'token with user_id: {decoded['user_id']} verified')
    return decoded['user_id'], None
