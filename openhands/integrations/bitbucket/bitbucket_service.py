import base64
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
        if base_domain:
            self.BASE_URL = f'https://api.{base_domain}/2.0'

    @property
    def provider(self) -> str:
        return ProviderType.BITBUCKET.value

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user."""
        return self.token

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def _get_bitbucket_headers(self) -> dict[str, str]:
        """Get headers for Bitbucket API requests."""
        token_value = self.token.get_secret_value()

        # Check if the token contains a colon, which indicates it's in username:password format
        if ':' in token_value:
            auth_str = base64.b64encode(token_value.encode()).decode()
            return {
                'Authorization': f'Basic {auth_str}',
                'Accept': 'application/json',
            }
        else:
            return {
                'Authorization': f'Bearer {token_value}',
                'Accept': 'application/json',
            }

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

        """
        try:
            async with httpx.AsyncClient() as client:
                bitbucket_headers = await self._get_bitbucket_headers()
                response = await self.execute_request(
                    client, url, bitbucket_headers, params, method
                )
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    bitbucket_headers = await self._get_bitbucket_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=bitbucket_headers,
                        params=params,
                        method=method,
                    )
                response.raise_for_status()
                return response.json(), dict(response.headers)
        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def get_user(self) -> User:
        """Get the authenticated user's information."""
        url = f'{self.BASE_URL}/user'
        data, _ = await self._make_request(url)

        account_id = data.get('account_id', '')

        return User(
            id=account_id,
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
        """Search for repositories."""
        # Bitbucket doesn't have a dedicated search endpoint like GitHub
        return []

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user using workspaces endpoint.

        This method gets all repositories (both public and private) that the user has access to
        by iterating through their workspaces and fetching repositories from each workspace.
        This approach is more comprehensive and efficient than the previous implementation
        that made separate calls for public and private repositories.
        """
        repositories = []

        # Get user's workspaces
        workspaces_url = f'{self.BASE_URL}/workspaces'
        workspaces_data, _ = await self._make_request(workspaces_url)

        for workspace in workspaces_data.get('values', []):
            workspace_slug = workspace.get('slug')
            if not workspace_slug:
                continue

            # Get repositories for this workspace
            workspace_repos_url = f'{self.BASE_URL}/repositories/{workspace_slug}'

            # Map sort parameter to Bitbucket API compatible values
            bitbucket_sort = sort
            if sort == 'pushed':
                # Bitbucket doesn't support 'pushed', use 'updated_on' instead
                bitbucket_sort = 'updated_on'

            params = {
                'pagelen': 100,
                'sort': bitbucket_sort,
            }
            repos_data, headers = await self._make_request(workspace_repos_url, params)

            for repo in repos_data.get('values', []):
                uuid = repo.get('uuid', '')
                repositories.append(
                    Repository(
                        id=uuid,
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
        """Get suggested tasks for the authenticated user across all repositories."""
        # TODO: implemented suggested tasks
        return []

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets all repository details from repository name."""
        # Extract owner and repo from the repository string (e.g., "owner/repo")
        parts = repository.split('/')
        if len(parts) < 2:
            raise ValueError(f'Invalid repository name: {repository}')

        owner = parts[-2]
        repo = parts[-1]

        url = f'{self.BASE_URL}/repositories/{owner}/{repo}'
        data, _ = await self._make_request(url)

        uuid = data.get('uuid', '')
        return Repository(
            id=uuid,
            full_name=f'{data.get("workspace", {}).get("slug", "")}/{data.get("slug", "")}',
            git_provider=ProviderType.BITBUCKET,
            is_public=data.get('is_private', True) is False,
            stargazers_count=None,  # Bitbucket doesn't have stars
            pushed_at=data.get('updated_on'),
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository."""
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

    async def create_pr(
        self,
        repo_name: str,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str | None = None,
        draft: bool = False,
    ) -> str:
        """Creates a pull request in Bitbucket.

        Args:
            repo_name: The repository name in the format "workspace/repo"
            source_branch: The source branch name
            target_branch: The target branch name
            title: The title of the pull request
            body: The description of the pull request
            draft: Whether to create a draft pull request

        Returns:
            The URL of the created pull request
        """
        # Extract owner and repo from the repository string (e.g., "owner/repo")
        parts = repo_name.split('/')
        if len(parts) < 2:
            raise ValueError(f'Invalid repository name: {repo_name}')

        owner = parts[-2]
        repo = parts[-1]

        url = f'{self.BASE_URL}/repositories/{owner}/{repo}/pullrequests'

        payload = {
            'title': title,
            'description': body or '',
            'source': {'branch': {'name': source_branch}},
            'destination': {'branch': {'name': target_branch}},
            'close_source_branch': False,
            'draft': draft,
        }

        data, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        # Return the URL to the pull request
        return data.get('links', {}).get('html', {}).get('href', '')
