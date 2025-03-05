from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.provider import ProviderHandler
from openhands.integrations.service_types import (
    AuthenticationError,
    Repository,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.server.auth import get_idp_token, get_provider_tokens, get_user_id

app = APIRouter(prefix='/api/github')


@app.get('/repositories', response_model=list[Repository])
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_user_id: str | None = Depends(get_user_id),
    provider_tokens: SecretStr | None = Depends(get_provider_tokens),
    idp_token: SecretStr | None = Depends(get_idp_token),
):
    if provider_tokens:
        client = GithubServiceImpl(
            user_id=github_user_id, idp_token=idp_token, token=None
        )
        try:
            repos: list[Repository] = await client.get_repositories(
                page, per_page, sort, installation_id
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


@app.get('/user', response_model=User)
async def get_github_user(
    github_user_id: str | None = Depends(get_user_id),
    provider_tokens: SecretStr | None = Depends(get_provider_tokens),
    idp_token: SecretStr | None = Depends(get_idp_token),
):
    if provider_tokens:
        client = ProviderHandler(provider_tokens=provider_tokens,
                                 idp_token=idp_token)

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
        content='GitHub token required.',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/installations', response_model=list[int])
async def get_github_installation_ids(
    github_user_id: str | None = Depends(get_user_id),
    provider_tokens: SecretStr | None = Depends(get_provider_tokens),
    idp_token: SecretStr | None = Depends(get_idp_token),
):
    if provider_tokens:
        client = GithubServiceImpl(
            user_id=github_user_id, idp_token=idp_token, token=None
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
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_user_id: str | None = Depends(get_user_id),
    provider_tokens: SecretStr | None = Depends(get_provider_tokens),
    idp_token: SecretStr | None = Depends(get_idp_token),
):
    if provider_tokens:
        client = GithubServiceImpl(
            user_id=github_user_id, idp_token=idp_token, token=None
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
    github_user_id: str | None = Depends(get_user_id),
    provider_tokens: SecretStr | None = Depends(get_provider_tokens),
    idp_token: SecretStr | None = Depends(get_idp_token),
):
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """

    if provider_tokens:
        client = GithubServiceImpl(
            user_id=github_user_id, idp_token=idp_token, token=None
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
