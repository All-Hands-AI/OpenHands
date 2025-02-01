from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openhands.server.services.github_service import GitHubService
from openhands.server.shared import SettingsStoreImpl, config, server_config
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api/github')


async def get_user_token(user_id: str):
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    if settings and settings.github_token:
        return settings.github_token.get_secret_value()

    return ''


def require_user_id(request: Request):
    github_user = get_github_user(request)
    if not github_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing GitHub token',
        )

    return github_user


GithubServiceImpl = get_impl(GitHubService, server_config.github_service_class)


@app.get('/repositories')
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_user_id: str | None = Depends(require_user_id),
):
    client = GithubServiceImpl(github_user_id)
    return await client.get_repositories(page, per_page, sort, installation_id)


@app.get('/user')
async def get_github_user(
    github_user_id: str | None = Depends(require_user_id),
):
    client = GithubServiceImpl(github_user_id)
    return await client.get_user()


@app.get('/installations')
async def get_github_installation_ids(
    github_user_id: str | None = Depends(require_user_id),
):
    client = GithubServiceImpl(github_user_id)
    installations_ids = await client.get_installation_ids()
    return JSONResponse(content=installations_ids)


@app.get('/search/repositories')
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_user_id: str | None = Depends(require_user_id),
):
    client = GithubServiceImpl(github_user_id)
    response = await client.search_repositories(query, per_page, sort, order)
    json_response = JSONResponse(content=response.json())
    response.close()
    return json_response
