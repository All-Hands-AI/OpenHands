from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import SecretStr
from sqlalchemy import select

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
    ProviderType,
)
from openhands.integrations.service_types import (
    AuthenticationError,
    Repository,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.server.auth import get_access_token, get_provider_tokens, get_user_id
from openhands.server.shared import server_config
from openhands.server.db import database
from openhands.server.models import User as UserModel

app = APIRouter(prefix='/api/user')


@app.get('/repositories', response_model=list[Repository])
async def get_user_repositories(
    sort: str = 'pushed',
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
):
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )

        try:
            repos: list[Repository] = await client.get_repositories(
                sort, server_config.app_mode
            )
            return repos

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/info', response_model=User)
async def get_user(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
):
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )

        try:
            user: User = await client.get_user()
            return user

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/installations', response_model=list[int])
async def get_github_installation_ids(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
):
    if provider_tokens and ProviderType.GITHUB in provider_tokens:
        token = provider_tokens[ProviderType.GITHUB]

        client = GithubServiceImpl(
            user_id=token.user_id, external_auth_token=access_token, token=token.token
        )
        try:
            installations_ids: list[int] = await client.get_installation_ids()
            return installations_ids

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return JSONResponse(
        content='GitHub token required.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/search/repositories', response_model=list[Repository])
async def search_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
):
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )
        try:
            repos: list[Repository] = await client.search_repositories(
                query, per_page, sort, order
            )
            return repos

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return JSONResponse(
        content='GitHub token required.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/suggested-tasks', response_model=list[SuggestedTask])
async def get_suggested_tasks(
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
):
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """

    if provider_tokens and ProviderType.GITHUB in provider_tokens:
        token = provider_tokens[ProviderType.GITHUB]

        client = GithubServiceImpl(
            user_id=token.user_id, external_auth_token=access_token, token=token.token
        )
        try:
            tasks: list[SuggestedTask] = await client.get_suggested_tasks()
            return tasks

        except AuthenticationError as e:
            return JSONResponse(
                content=str(e),
                status_code=401,
            )

        except UnknownException as e:
            return JSONResponse(
                content=str(e),
                status_code=500,
            )

    return JSONResponse(
        content='GitHub token required.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/status', response_model=dict)
async def get_user_status(request: Request):
    """Get the current user's status (activated or non_activated)"""
    user_id = get_user_id(request)
    if not user_id:
        return JSONResponse(
            content={'error': 'User not authenticated'},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    
    # Query the user record to get status
    query = select(UserModel).where(UserModel.c.public_key == user_id.lower())
    user = await database.fetch_one(query)
    
    if not user:
        return JSONResponse(
            content={'error': 'User not found'},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    return {
        'status': user['status'],
        'activated': user['status'] == 'activated'
    }
