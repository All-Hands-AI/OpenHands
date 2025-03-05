import os
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    AuthenticationError,
    GitService,
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
        idp_token: SecretStr | None = None,
        token: SecretStr | None = None,
    ):
        self.user_id = user_id

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

    async def get_latest_token(self) -> SecretStr:
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

    async def search_repositories(self, query, per_page, sort, order):
        return await super().search_repositories(query, per_page, sort, order)


gitlab_service_cls = os.environ.get(
    'OPENHANDS_GITLAB_SERVICE_CLS',
    'openhands.integrations.gitlab.gitlab_service.GitLabService',
)
GitLabServiceImpl = get_impl(GitLabService, gitlab_service_cls)