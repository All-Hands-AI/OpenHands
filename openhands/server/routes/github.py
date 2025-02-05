from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_github_token, get_user_id
from openhands.server.services.github_service import GitHubService
from openhands.server.shared import server_config
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api/github')


def require_github_token(request: Request):
    github_token = get_github_token(request)
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing GitHub token',
        )

    return github_token


GithubServiceImpl = get_impl(GitHubService, server_config.github_service_class)


@app.get('/repositories')
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_token: str = Depends(require_github_token),
    github_user_id: str | None = Depends(get_user_id),
):
    try:
        client = GithubServiceImpl(github_token, github_user_id)
        return await client.fetch_response(
            'get_repositories', page, per_page, sort, installation_id
        )
    except Exception as e:
        logger.error("Couldn't get GitHub repositories")
        logger.error(e)
        raise


@app.get('/user')
async def get_github_user(
    github_token: str = Depends(require_github_token),
    github_user_id: str | None = Depends(get_user_id),
):
    try:
        client = GithubServiceImpl(github_token, github_user_id)
        return await client.fetch_response('get_user')
    except Exception as e:
        logger.error("Couldn't get GitHub user")
        logger.error(e)
        raise


@app.get('/installations')
async def get_github_installation_ids(
    github_token: str = Depends(require_github_token),
    github_user_id: str | None = Depends(get_user_id),
):
    try:
        client = GithubServiceImpl(github_token, github_user_id)
        installations = await client.get_installation_ids()
        return JSONResponse(content=[i['id'] for i in installations])
    except Exception as e:
        logger.error("Couldn't get GitHub installations")
        logger.error(e)
        raise


@app.get('/search/repositories')
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_token: str = Depends(require_github_token),
    github_user_id: str | None = Depends(get_user_id),
):
    try:
        client = GithubServiceImpl(github_token, github_user_id)
        response = await client.search_repositories(query, per_page, sort, order)
        json_response = JSONResponse(content=response.json())
        response.close()
        return json_response
    except Exception as e:
        logger.error("Couldn't search GitHub repositories")
        logger.error(e)
        raise
