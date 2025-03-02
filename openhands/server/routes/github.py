from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.github.github_types import (
    GhAuthenticationError,
    GHUnknownException,
    GitHubRepository,
    GitHubUser,
    SuggestedTask,
)
from openhands.server.auth import get_token, get_token_type, get_idp_token, get_user_id

app = APIRouter(prefix='/api/github')


@app.get('/repositories', response_model=list[GitHubRepository], responses={
    401: {"model": None},
    500: {"model": None},
})
async def get_github_repositories(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_token),
    idp_token: SecretStr | None = Depends(get_idp_token),
) -> Response:
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type != 'github':
        return JSONResponse(
            content='Invalid token type. GitHub token required.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    client = GithubServiceImpl(
        user_id=github_user_id, idp_token=idp_token, token=token
    )
    try:
        repos: list[GitHubRepository] = await client.get_repositories(
            page, per_page, sort, installation_id
        )
        return JSONResponse(content=[repo.model_dump() for repo in repos])

    except GhAuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except GHUnknownException as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get('/user', response_model=GitHubUser, responses={
    401: {"model": None},
    500: {"model": None},
})
async def get_github_user(
    request: Request,
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_token),
    idp_token: SecretStr | None = Depends(get_idp_token),
) -> Response:
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type != 'github':
        return JSONResponse(
            content='Invalid token type. GitHub token required.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    client = GithubServiceImpl(
        user_id=github_user_id, idp_token=idp_token, token=token
    )
    try:
        user: GitHubUser = await client.get_user()
        return JSONResponse(content=user.model_dump())

    except GhAuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except GHUnknownException as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get('/installations', response_model=list[int], responses={
    401: {"model": None},
    500: {"model": None},
})
async def get_github_installation_ids(
    request: Request,
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_token),
    idp_token: SecretStr | None = Depends(get_idp_token),
) -> Response:
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type != 'github':
        return JSONResponse(
            content='Invalid token type. GitHub token required.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    client = GithubServiceImpl(
        user_id=github_user_id, idp_token=idp_token, token=token
    )
    try:
        installations_ids: list[int] = await client.get_installation_ids()
        return JSONResponse(content=installations_ids)

    except GhAuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except GHUnknownException as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get('/search/repositories', response_model=list[GitHubRepository], responses={
    401: {"model": None},
    500: {"model": None},
})
async def search_github_repositories(
    request: Request,
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_token),
    idp_token: SecretStr | None = Depends(get_idp_token),
) -> Response:
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type != 'github':
        return JSONResponse(
            content='Invalid token type. GitHub token required.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    client = GithubServiceImpl(
        user_id=github_user_id, idp_token=idp_token, token=token
    )
    try:
        repos: list[GitHubRepository] = await client.search_repositories(
            query, per_page, sort, order
        )
        return JSONResponse(content=[repo.model_dump() for repo in repos])

    except GhAuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    except GHUnknownException as e:
        return JSONResponse(
            content=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get('/suggested-tasks', response_model=list[SuggestedTask], responses={
    401: {"model": None},
    500: {"model": None},
})
async def get_suggested_tasks(
    request: Request,
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_token),
    idp_token: SecretStr | None = Depends(get_idp_token),
) -> Response:
    """Get suggested tasks for the authenticated user across their most recently pushed repositories.

    Returns:
    - PRs owned by the user
    - Issues assigned to the user.
    """
    token = get_token(request)
    token_type = get_token_type(request)
    if token_type != 'github':
        return JSONResponse(
            content='Invalid token type. GitHub token required.',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    client = GithubServiceImpl(
        user_id=github_user_id, idp_token=idp_token, token=token
    )
    try:
        tasks: list[SuggestedTask] = await client.get_suggested_tasks()
        return JSONResponse(content=[task.model_dump() for task in tasks])

    except GhAuthenticationError as e:
        return JSONResponse(
            content=str(e),
            status_code=401,
        )

    except GHUnknownException as e:
        return JSONResponse(
            content=str(e),
            status_code=500,
        )