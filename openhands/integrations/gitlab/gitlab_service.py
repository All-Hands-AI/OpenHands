import os
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
    Repository,
    UnknownException,
    User,
)
from openhands.utils.import_utils import get_impl


class GitLabService(GitService):
    BASE_URL = 'https://gitlab.com/api/v4'
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

    async def _get_gitlab_headers(self) -> dict:
        """
        Retrieve the GitLab Token to construct the headers
        """
        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'Bearer {self.token.get_secret_value()}',
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
                gitlab_headers = await self._get_gitlab_headers()
                response = await client.get(url, headers=gitlab_headers, params=params)
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    gitlab_headers = await self._get_gitlab_headers()
                    response = await client.get(
                        url, headers=gitlab_headers, params=params
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid GitLab token')
            raise UnknownException('Unknown error')

        except httpx.HTTPError:
            raise UnknownException('Unknown error')

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._fetch_data(url)

        return User(
            id=response.get('id'),
            username=response.get('username'),
            avatar_url=response.get('avatar_url'),
            name=response.get('name'),
            email=response.get('email'),
            company=response.get('organization'),
            login=response.get('username'),
        )

    async def search_repositories(
        self, query: str, per_page: int = 30, sort: str = 'updated', order: str = 'desc'
    ):
        url = f'{self.BASE_URL}/search'
        params = {
            'scope': 'projects',
            'search': query,
            'per_page': per_page,
            'order_by': sort,
            'sort': order,
        }
        response, headers = await self._fetch_data(url, params)
        return response, headers

    async def get_repositories(
        self, page: int, per_page: int, sort: str, installation_id: int | None
    ) -> list[Repository]:
        return []


gitlab_service_cls = os.environ.get(
    'OPENHANDS_GITLAB_SERVICE_CLS',
    'openhands.integrations.gitlab.gitlab_service.GitLabService',
)
GitLabServiceImpl = get_impl(GitLabService, gitlab_service_cls)
