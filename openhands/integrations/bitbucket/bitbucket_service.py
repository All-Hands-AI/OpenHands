import os
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    GitService,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    UnknownException,
    User,
)
from openhands.server.types import AppMode


class BitbucketService(BaseGitService, GitService):
    """Default implementation of GitService for Bitbucket integration.

    This is an extension point in OpenHands that allows applications to customize Bitbucket
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.bitbucket_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

    BASE_URL = 'https://api.bitbucket.org/2.0'
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager
        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.base_domain = base_domain or 'bitbucket.org'

        if token:
            self.token = token
        elif os.environ.get('BITBUCKET_TOKEN'):
            self.token = SecretStr(os.environ.get('BITBUCKET_TOKEN', ''))

    @property
    def provider(self) -> str:
        return 'Bitbucket'

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user"""
        if self.external_token_manager and self.external_auth_id:
            # This would be implemented by a custom token manager
            return None
        return self.token

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make a request to the Bitbucket API.

        Args:
            url: The URL to request
            params: Optional parameters for the request
            method: The HTTP method to use

        Returns:
            A tuple of (response_data, response_headers)

        Raises:
            AuthenticationError: If the token is invalid
            RateLimitError: If the rate limit is exceeded
            UnknownException: For other errors
        """
        headers = {
            'Authorization': f'Bearer {self.token.get_secret_value()}',
            'Accept': 'application/json',
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await self.execute_request(
                    client, url, headers, params, method
                )
                response.raise_for_status()
                return response.json(), dict(response.headers)
        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)
        except Exception as e:
            raise UnknownException(f'Unknown error: {e}')

    async def get_user(self) -> User:
        """Get the authenticated user's information"""
        url = f'{self.BASE_URL}/user'
        data, _ = await self._make_request(url)

        return User(
            id=data.get('account_id', 0),
            login=data.get('username', ''),
            avatar_url=data.get('links', {}).get('avatar', {}).get('href', ''),
            name=data.get('display_name'),
            email=None,  # Bitbucket API doesn't return email in this endpoint
        )

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        """Search for repositories"""
        # Bitbucket doesn't have a dedicated search endpoint like GitHub
        # We'll use the repositories endpoint and filter client-side
        url = f'{self.BASE_URL}/repositories'
        params = {
            'q': query,
            'pagelen': per_page,
            'sort': sort,
        }

        data, headers = await self._make_request(url, params)

        repositories = []
        for repo in data.get('values', []):
            repositories.append(
                Repository(
                    id=repo.get('uuid', ''),
                    full_name=f'{repo.get("workspace", {}).get("slug", "")}/{repo.get("slug", "")}',
                    git_provider=ProviderType.BITBUCKET,
                    is_public=repo.get('is_private', True) is False,
                    stargazers_count=None,  # Bitbucket doesn't have stars
                    link_header=headers.get('Link', ''),
                    pushed_at=repo.get('updated_on'),
                )
            )

        return repositories

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user"""
        url = f'{self.BASE_URL}/repositories'
        params = {
            'role': 'member',
            'pagelen': 100,
            'sort': sort,
        }

        data, headers = await self._make_request(url, params)

        repositories = []
        for repo in data.get('values', []):
            repositories.append(
                Repository(
                    id=repo.get('uuid', ''),
                    full_name=f'{repo.get("workspace", {}).get("slug", "")}/{repo.get("slug", "")}',
                    git_provider=ProviderType.BITBUCKET,
                    is_public=repo.get('is_private', True) is False,
                    stargazers_count=None,  # Bitbucket doesn't have stars
                    link_header=headers.get('Link', ''),
                    pushed_at=repo.get('updated_on'),
                )
            )

        return repositories

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories"""
        # This would require multiple API calls to get PRs with conflicts, failing checks, etc.
        # For now, we'll return an empty list
        return []

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets all repository details from repository name"""
        # Extract owner and repo from the repository string (e.g., "owner/repo")
        parts = repository.split('/')
        if len(parts) < 2:
            raise ValueError(f'Invalid repository name: {repository}')

        owner = parts[-2]
        repo = parts[-1]

        url = f'{self.BASE_URL}/repositories/{owner}/{repo}'
        data, _ = await self._make_request(url)

        return Repository(
            id=data.get('uuid', ''),
            full_name=f'{data.get("workspace", {}).get("slug", "")}/{data.get("slug", "")}',
            git_provider=ProviderType.BITBUCKET,
            is_public=data.get('is_private', True) is False,
            stargazers_count=None,  # Bitbucket doesn't have stars
            pushed_at=data.get('updated_on'),
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""
        # Extract owner and repo from the repository string (e.g., "owner/repo")
        parts = repository.split('/')
        if len(parts) < 2:
            raise ValueError(f'Invalid repository name: {repository}')

        owner = parts[-2]
        repo = parts[-1]

        url = f'{self.BASE_URL}/repositories/{owner}/{repo}/refs/branches'
        data, _ = await self._make_request(url)

        branches = []
        for branch in data.get('values', []):
            branches.append(
                Branch(
                    name=branch.get('name', ''),
                    commit_sha=branch.get('target', {}).get('hash', ''),
                    protected=False,  # Bitbucket doesn't expose this in the API
                    last_push_date=branch.get('target', {}).get('date', None),
                )
            )

        return branches
