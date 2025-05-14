from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.provider import (
    PROVIDER_TOKEN_TYPE,
    ProviderHandler,
)
from openhands.integrations.service_types import (
    AuthenticationError,
    Branch,
    Repository,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.server.shared import config as app_config
from openhands.server.shared import server_config
from openhands.server.user_auth import (
    get_access_token,
    get_provider_tokens,
    get_user_id,
)

app = APIRouter(prefix='/api/user')


@app.get('/repositories', response_model=list[Repository])
async def get_user_repositories(
    sort: str = 'pushed',
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> list[Repository] | JSONResponse:
    client = ProviderHandler(
        provider_tokens=provider_tokens,
        external_auth_token=access_token,
        external_auth_id=user_id,
        config=app_config,
    )

    try:
        return await client.get_repositories(sort, server_config.app_mode)

    except AuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


@app.get('/info', response_model=User)
async def get_user(
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
    user_id: str | None = Depends(get_user_id),
) -> User | JSONResponse:
    # Check if any provider is connected (including local provider)
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens,
            external_auth_token=access_token,
            external_auth_id=user_id,
            config=app_config,
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

    # Check if local git provider should be available
    if app_config.workspace_base:
        # Return a placeholder user for local git provider
        return User(
            id=0,
            login='local-user',
            avatar_url='',
            company=None,
            name='Local Git User',
            email=None,
        )

    return JSONResponse(
        content='Git provider token required. (such as GitHub).',
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.get('/search/repositories', response_model=list[Repository])
async def search_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
) -> list[Repository] | JSONResponse:
    client = ProviderHandler(
        provider_tokens=provider_tokens,
        external_auth_token=access_token,
        config=app_config,
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


@app.get('/suggested-tasks', response_model=list[SuggestedTask])
async def get_suggested_tasks(
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
) -> list[SuggestedTask] | JSONResponse:
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """
    client = ProviderHandler(
        provider_tokens=provider_tokens,
        external_auth_token=access_token,
        config=app_config,
    )
    tasks: list[SuggestedTask] = await client.get_suggested_tasks()
    return tasks


@app.get('/repository/branches', response_model=list[Branch])
async def get_repository_branches(
    repository: str,
    provider_tokens: PROVIDER_TOKEN_TYPE = Depends(get_provider_tokens),
    access_token: SecretStr | None = Depends(get_access_token),
) -> list[Branch] | JSONResponse:
    """Get branches for a repository.

    Args:
        repository: The repository name in the format 'owner/repo'

    Returns:
        A list of branches for the repository
    """
    if provider_tokens:
        client = ProviderHandler(
            provider_tokens=provider_tokens, external_auth_token=access_token
        )
        try:
            branches: list[Branch] = await client.get_branches(repository)
            return branches

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
