from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import SecretStr

from openhands.integrations.github.github_service import GithubServiceImpl
from openhands.integrations.github.github_types import (
    GhAuthenticationError,
    GHUnknownException,
    GitHubRepository,
    GitHubUser,
)
from openhands.server.auth import get_github_token, get_user_id

app = APIRouter(prefix='/api/github')


@app.get('/repositories')
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_github_token),
):
    client = GithubServiceImpl(user_id=github_user_id, token=github_user_token)
    try:
        repos: list[GitHubRepository] = await client.get_repositories(
            page, per_page, sort, installation_id
        )
        return repos

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


@app.get('/user')
async def get_github_user(
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_github_token),
):
    client = GithubServiceImpl(user_id=github_user_id, token=github_user_token)
    try:
        user: GitHubUser = await client.get_user()
        return user

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


@app.get('/installations')
async def get_github_installation_ids(
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_github_token),
):
    client = GithubServiceImpl(user_id=github_user_id, token=github_user_token)
    try:
        installations_ids: list[int] = await client.get_installation_ids()
        return installations_ids

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


@app.get('/search/repositories')
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_user_id: str | None = Depends(get_user_id),
    github_user_token: SecretStr | None = Depends(get_github_token),
):
    client = GithubServiceImpl(user_id=github_user_id, token=github_user_token)
    try:
        repos: list[GitHubRepository] = await client.search_repositories(
            query, per_page, sort, order
        )
        return repos

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
