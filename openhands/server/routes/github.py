import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from github import Github
from github.AuthenticatedUser import AuthenticatedUser
from github.GithubException import GithubException
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.Repository import Repository

from openhands.server.auth import get_github_token
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api/github')


def require_github_token(request: Request):
    github_token = get_github_token(request)
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing GitHub token',
        )

    return github_token


@app.get('/repositories')
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_token: str = Depends(require_github_token),
):
    try:
        with Github(github_token) as gh:
            gh.per_page = per_page
            gh_user: NamedUser | AuthenticatedUser = await call_sync_from_async(
                gh.get_user
            )

            repos_list: PaginatedList[Repository] = await call_sync_from_async(
                gh_user.get_repos, sort
            )

            repos: list[Repository] = await call_sync_from_async(
                repos_list.get_page, page - 1
            )
            repos = [repo.raw_data for repo in repos]

            json_response = JSONResponse(content=repos)

            # PyGitHub does not expose next link header, we construct it by checking if we've reach total expected count
            if (page - 1) * 30 + len(repos) < repos_list.totalCount:
                next_page_url = f'<https://api.github.com/user/repos?page={page+1}&per_page=30>; rel="next",'
                json_response.headers['Link'] = next_page_url

            return json_response

    except GithubException as e:
        raise HTTPException(
            status_code=e.status if e else 500,
            detail=f'Error fetching user: {str(e)}',
        )


@app.get('/user')
async def get_github_user(github_token: str = Depends(require_github_token)):
    try:
        with Github(github_token) as gh:
            gh_user: NamedUser | AuthenticatedUser = await call_sync_from_async(
                gh.get_user
            )
            return JSONResponse(content=gh_user.raw_data)
    except GithubException as e:
        raise HTTPException(
            status_code=e.status if e else 500,
            detail=f'Error fetching user: {str(e)}',
        )


@app.get('/installations')
async def get_github_installation_ids(
    github_token: str = Depends(require_github_token),
):
    headers = generate_github_headers(github_token)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.github.com/user/installations', headers=headers
            )
            response.raise_for_status()
            data = response.json()
            ids = [installation['id'] for installation in data['installations']]
            return JSONResponse(content=ids)

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, 'response') else 500,
            detail=f'Error fetching installations: {str(e)}',
        )


@app.get('/search/repositories')
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_token: str = Depends(require_github_token),
):
    try:
        with Github(github_token) as gh:
            gh.per_page = per_page
            repos_list: PaginatedList[Repository] = await call_sync_from_async(
                gh.search_repositories, query, sort, order
            )

            repos: list[Repository] = await call_sync_from_async(repos_list.get_page, 0)

            repos = [repo.raw_data for repo in repos]

            print('repos', repos)
            return JSONResponse(content=repos)

    except GithubException as e:
        raise HTTPException(
            status_code=e.status if e else 500,
            detail=f'Error fetching user: {str(e)}',
        )


def generate_github_headers(token: str) -> dict[str, str]:
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
