import httpx
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from openhands.server.auth import get_github_token
from openhands.server.shared import server_config
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


class GithubClient:
    BASE_URL = 'https://api.github.com'

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def should_refresh(self, status_code: int):
        if server_config.app_mode == 'SAAS' and status_code == 401:
            return True

        return False

    async def _refresh_token(self):
        pass

    async def _fetch_data(self, url: str, params: dict | None = None):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                if self.should_refresh(response.status_code):
                    await self._refresh_token()
                    response = await client.get(
                        url, headers=self.headers, params=params
                    )
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = e.response.text
            raise HTTPException(
                status_code=status_code,
                detail=f'GitHub API error: {error_detail}',
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f'HTTP error: {str(e)}')

    async def get_user(self):
        url = f'{self.BASE_URL}/user'
        return await self._fetch_data(url)

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ):
        params = {'page': str(page), 'per_page': str(per_page)}
        if installation_id:
            url = f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
        else:
            url = f'{self.BASE_URL}/user/repos'
            params['sort'] = sort
        return await self._fetch_data(url, params)

    async def get_installation_ids(self):
        url = f'{self.BASE_URL}/user/installations'
        response = await self._fetch_data(url)
        data = response.json()
        return data.get('installations', [])

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ):
        url = f'{self.BASE_URL}/search/repositories'
        params = {'q': query, 'per_page': per_page, 'sort': sort, 'order': order}
        return await call_sync_from_async(
            requests.get, url, headers=self.headers, params=params
        )

    async def fetch_response(self, method: str, *args, **kwargs):
        response = await getattr(self, method)(*args, **kwargs)
        json_response = JSONResponse(
            content=response.json(), status_code=response.status_code
        )
        if 'Link' in response.headers:
            json_response.headers['Link'] = response.headers['Link']
        return json_response


@app.get('/repositories')
async def get_github_repositories(
    page: int = 1,
    per_page: int = 10,
    sort: str = 'pushed',
    installation_id: int | None = None,
    github_token: str = Depends(require_github_token),
):
    client = GithubClient(github_token)
    return await client.fetch_response(
        'get_repositories', page, per_page, sort, installation_id
    )


@app.get('/user')
async def get_github_user(github_token: str = Depends(require_github_token)):
    client = GithubClient(github_token)
    return await client.fetch_response('get_user')


@app.get('/installations')
async def get_github_installation_ids(
    github_token: str = Depends(require_github_token),
):
    client = GithubClient(github_token)
    installations = await client.get_installation_ids()
    return JSONResponse(content=[i['id'] for i in installations])


@app.get('/search/repositories')
async def search_github_repositories(
    query: str,
    per_page: int = 5,
    sort: str = 'stars',
    order: str = 'desc',
    github_token: str = Depends(require_github_token),
):
    client = GithubClient(github_token)
    response = await client.search_repositories(query, per_page, sort, order)
    json_response = JSONResponse(content=response.json())
    response.close()
    return json_response
