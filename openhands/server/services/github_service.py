from typing import Any

import httpx
from fastapi import Request

from openhands.server.auth import get_github_token
from openhands.server.data_models.gh_types import GitHubRepository, GitHubUser
from openhands.server.shared import SettingsStoreImpl, config, server_config
from openhands.server.types import AppMode, GhAuthenticationError, GHUnknownException


class GitHubService:
    BASE_URL = 'https://api.github.com'
    token: str = ''

    def __init__(self, user_id: str | None):
        self.user_id = user_id

    async def _get_github_headers(self):
        """
        Retrieve the GH Token from settings store to construct the headers
        """

        settings_store = await SettingsStoreImpl.get_instance(config, self.user_id)
        settings = await settings_store.load()
        if settings and settings.github_token:
            self.token = settings.github_token.get_secret_value()

        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def _has_token_expired(self, status_code: int):
        return status_code == 401

    async def _get_latest_token(self):
        pass

    async def _fetch_data(
        self, url: str, params: dict | None = None
    ) -> tuple[Any, dict]:
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_github_headers()
                response = await client.get(url, headers=github_headers, params=params)
                if server_config.app_mode == AppMode.SAAS and self._has_token_expired(
                    response.status_code
                ):
                    await self._get_latest_token()
                    github_headers = await self._get_github_headers()
                    response = await client.get(
                        url, headers=github_headers, params=params
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError:
            raise GhAuthenticationError('Invalid Github token')

        except httpx.HTTPError:
            raise GHUnknownException('Unknown error')

    async def get_user(self) -> GitHubUser:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._fetch_data(url)

        return GitHubUser(
            id=response.get('id'),
            login=response.get('login'),
            avatar_url=response.get('avatar_url'),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )

    async def validate_user(self, token) -> GitHubUser:
        self.token = token
        return await self.get_user()

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ) -> list[GitHubRepository]:
        params = {'page': str(page), 'per_page': str(per_page)}
        if installation_id:
            url = f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
            response, headers = await self._fetch_data(url, params)
            response = response.get('repositories', [])
        else:
            url = f'{self.BASE_URL}/user/repos'
            params['sort'] = sort
            response, headers = await self._fetch_data(url, params)

        next_link: str = headers.get('Link', '')
        repos = [
            GitHubRepository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
                link_header=next_link,
            )
            for repo in response
        ]
        return repos

    async def get_installation_ids(self) -> list[int]:
        url = f'{self.BASE_URL}/user/installations'
        response, _ = await self._fetch_data(url)
        installations = response.get('installations', [])
        return [i['id'] for i in installations]

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ) -> list[GitHubRepository]:
        url = f'{self.BASE_URL}/search/repositories'
        params = {'q': query, 'per_page': per_page, 'sort': sort, 'order': order}

        response, _ = await self._fetch_data(url, params)
        repos = response.get('items', [])

        repos = [
            GitHubRepository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
            )
            for repo in repos
        ]

        return repos

    @classmethod
    def get_gh_token(cls, request: Request) -> str | None:
        return get_github_token(request)
