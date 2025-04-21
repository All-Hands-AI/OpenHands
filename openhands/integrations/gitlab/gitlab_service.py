import os
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
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


class GitLabService(GitService):
    BASE_URL = 'https://gitlab.com/api/v4'
    GRAPHQL_URL = 'https://gitlab.com/api/graphql'
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

    async def _get_gitlab_headers(self) -> dict[str, Any]:
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

            logger.warning(f'Status error on GL API: {e}')
            raise UnknownException('Unknown error')

        except httpx.HTTPError as e:
            logger.warning(f'HTTP error on GL API: {e}')
            raise UnknownException('Unknown error')

    async def execute_graphql_query(self, query: str, variables: dict[str, Any]) -> Any:
        """
        Execute a GraphQL query against the GitLab GraphQL API

        Args:
            query: The GraphQL query string
            variables: Optional variables for the GraphQL query

        Returns:
            The data portion of the GraphQL response
        """
        try:
            async with httpx.AsyncClient() as client:
                gitlab_headers = await self._get_gitlab_headers()
                # Add content type header for GraphQL
                gitlab_headers['Content-Type'] = 'application/json'

                payload = {
                    'query': query,
                    'variables': variables,
                }

                response = await client.post(
                    self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                )

                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    gitlab_headers = await self._get_gitlab_headers()
                    gitlab_headers['Content-Type'] = 'application/json'
                    response = await client.post(
                        self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                    )

                response.raise_for_status()
                result = response.json()

                # Check for GraphQL errors
                if 'errors' in result:
                    error_message = result['errors'][0].get(
                        'message', 'Unknown GraphQL error'
                    )
                    raise UnknownException(f'GraphQL error: {error_message}')

                return result.get('data')
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid GitLab token')

            logger.warning(f'Status error on GL API: {e}')
            raise UnknownException('Unknown error')

        except httpx.HTTPError as e:
            logger.warning(f'HTTP error on GL API: {e}')
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
    ) -> list[Repository]:
        url = f'{self.BASE_URL}/projects'
        params = {
            'search': query,
            'per_page': per_page,
            'order_by': 'last_activity_at',
            'sort': order,
            'visibility': 'public',
        }

        response, _ = await self._fetch_data(url, params)
        repos = [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('path_with_namespace'),
                stargazers_count=repo.get('star_count'),
                git_provider=ProviderType.GITLAB,
            )
            for repo in response
        ]

        return repos

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by GitLab API
        all_repos: list[dict] = []
        page = 1

        url = f'{self.BASE_URL}/projects'
        # Map GitHub's sort values to GitLab's order_by values
        order_by = {
            'pushed': 'last_activity_at',
            'updated': 'last_activity_at',
            'created': 'created_at',
            'full_name': 'name',
        }.get(sort, 'last_activity_at')

        while len(all_repos) < MAX_REPOS:
            params = {
                'page': str(page),
                'per_page': str(PER_PAGE),
                'order_by': order_by,
                'sort': 'desc',  # GitLab uses sort for direction (asc/desc)
                'membership': 1,  # Use 1 instead of True
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
                full_name=repo.get('path_with_namespace'),
                stargazers_count=repo.get('star_count'),
                git_provider=ProviderType.GITLAB,
                is_public=repo.get('visibility') == 'public',
            )
            for repo in all_repos
        ]


gitlab_service_cls = os.environ.get(
    'OPENHANDS_GITLAB_SERVICE_CLS',
    'openhands.integrations.gitlab.gitlab_service.GitLabService',
)
GitLabServiceImpl = get_impl(GitLabService, gitlab_service_cls)
