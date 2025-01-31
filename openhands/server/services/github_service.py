import httpx
import requests
from fastapi.responses import JSONResponse

from openhands.server.shared import server_config
from openhands.utils.async_utils import call_sync_from_async


class GitHubService:
    BASE_URL = 'https://api.github.com'

    def __init__(self, token: str, user_id: str | None):
        self.token = token
        self.user_id = user_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def _has_token_expired(self, status_code: int):
        return status_code == 401

    async def _get_latest_token(self):
        pass

    async def _fetch_data(self, url: str, params: dict | None = None):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                if server_config.app_mode == 'SAAS' and self._has_token_expired(
                    response.status_code
                ):
                    await self._get_latest_token()
                    response = await client.get(
                        url, headers=self.headers, params=params
                    )
                response.raise_for_status()
                return response

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_detail = e.response.text

            return httpx.Response(
                status_code=status_code, json=f'GitHub API error: {error_detail}'
            )
        except httpx.HTTPError as e:
            return httpx.Response(status_code=500, json=f'HTTP error: {str(e)}')

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
