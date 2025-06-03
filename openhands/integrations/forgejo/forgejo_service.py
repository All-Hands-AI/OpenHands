import os
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
    ProviderType,
    Repository,
    UnknownException,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class ForgejoService(GitService):
    # Default to Codeberg, can be overridden
    DEFAULT_BASE_URL = 'https://codeberg.org/api/v1'
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_url: str | None = None,
        host: str | None = None,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

        # Set the base URL with the following priority:
        # 1. Explicitly provided base_url parameter
        # 2. host parameter from ProviderToken
        # 3. FORGEJO_BASE_URL environment variable
        # 4. Default Codeberg URL
        if base_url:
            self.base_url = base_url
        elif host:
            self.base_url = host
        else:
            self.base_url = os.environ.get('FORGEJO_BASE_URL', self.DEFAULT_BASE_URL)

    async def _get_forgejo_headers(self) -> dict:
        """
        Retrieve the Forgejo Token to construct the headers
        """
        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'token {self.token.get_secret_value()}',
            'Accept': 'application/json',
        }

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _fetch_data(
        self, url: str, params: dict | None = None
    ) -> tuple[Any, dict]:
        try:
            async with httpx.AsyncClient() as client:
                forgejo_headers = await self._get_forgejo_headers()
                response = await client.get(url, headers=forgejo_headers, params=params)
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    forgejo_headers = await self._get_forgejo_headers()
                    response = await client.get(
                        url, headers=forgejo_headers, params=params
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid Forgejo token')
            raise UnknownException(f'Unknown error: {e}')

        except httpx.HTTPError as e:
            raise UnknownException(f'HTTP error: {e}')

    async def get_user(self) -> User:
        url = f'{self.base_url}/user'
        response, _ = await self._fetch_data(url)

        return User(
            id=response.get('id'),
            username=response.get('username'),
            avatar_url=response.get('avatar_url'),
            name=response.get('full_name'),
            email=response.get('email'),
            company=response.get('organization'),
            login=response.get('username'),
        )

    async def search_repositories(
        self, query: str, per_page: int = 30, sort: str = 'updated', order: str = 'desc'
    ) -> list[Repository]:
        url = f'{self.base_url}/repos/search'
        params = {
            'q': query,
            'limit': per_page,
            'sort': sort,
            'order': order,
            'mode': 'source',  # Only return repositories that are not forks
        }

        response, _ = await self._fetch_data(url, params)
        repos = [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stars_count'),
                git_provider=ProviderType.FORGEJO,
                is_public=not repo.get('private', False),
            )
            for repo in response.get('data', [])
        ]

        return repos

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by Forgejo API
        all_repos: list[dict] = []
        page = 1

        url = f'{self.base_url}/user/repos'
        # Map GitHub's sort values to Forgejo's sort values
        sort_map = {
            'pushed': 'updated',
            'updated': 'updated',
            'created': 'created',
            'full_name': 'name',
        }
        forgejo_sort = sort_map.get(sort, 'updated')

        while len(all_repos) < MAX_REPOS:
            params = {
                'page': str(page),
                'limit': str(PER_PAGE),
                'sort': forgejo_sort,
            }
            response, headers = await self._fetch_data(url, params)

            if not response:  # No more repositories
                break

            all_repos.extend(response)
            page += 1

            # Check if we've reached the last page
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        # Trim to MAX_REPOS if needed and convert to Repository objects
        all_repos = all_repos[:MAX_REPOS]
        return [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stars_count'),
                git_provider=ProviderType.FORGEJO,
                is_public=not repo.get('private', False),
            )
            for repo in all_repos
        ]


forgejo_service_cls = os.environ.get(
    'OPENHANDS_FORGEJO_SERVICE_CLS',
    'openhands.integrations.forgejo.forgejo_service.ForgejoService',
)
ForgejoServiceImpl = get_impl(ForgejoService, forgejo_service_cls)
