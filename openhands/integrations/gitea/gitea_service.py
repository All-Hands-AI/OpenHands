import base64
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    GitService,
    OwnerType,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    TaskType,
    User,
)
from openhands.microagent.types import MicroagentContentResponse
from openhands.server.types import AppMode


class GiteaService(BaseGitService, GitService):
    """Implementation of GitService for Gitea integration.

    This service provides integration with Gitea instances, supporting both
    self-hosted and cloud-hosted Gitea installations. The API is largely
    compatible with GitHub's API v3, with some differences in endpoints
    and response formats.
    """

    BASE_URL = 'https://gitea.com/api/v1'  # Default for gitea.com
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

        if token:
            self.token = token

        if base_domain:
            # Check if protocol is already included
            if base_domain.startswith(('http://', 'https://')):
                # Use the provided protocol
                self.BASE_URL = f'{base_domain}/api/v1'
            else:
                # Default to https if no protocol specified
                self.BASE_URL = f'https://{base_domain}/api/v1'

        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token

    @property
    def provider(self) -> str:
        return ProviderType.GITEA.value

    async def _get_gitea_headers(self) -> dict:
        """Retrieve the Gitea Token to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'token {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/json',
        }

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        return f'{self.BASE_URL}/repos/{repository}/contents/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        return f'{self.BASE_URL}/repos/{repository}/contents/{microagents_path}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request."""
        return None  # Gitea doesn't need additional parameters

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return (
            item.get('type') == 'file'
            and item.get('name', '').endswith('.md')
            and not item.get('name', '').startswith('.')
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        return item.get('name', '')

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return item.get('path', '')

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make an HTTP request to the Gitea API."""
        headers = await self._get_gitea_headers()

        async with httpx.AsyncClient() as client:
            try:
                response = await self.execute_request(
                    client, url, headers, params, method
                )
                response.raise_for_status()

                # Parse response headers for pagination info
                response_headers = dict(response.headers)

                # Handle different content types
                if response.headers.get('content-type', '').startswith(
                    'application/json'
                ):
                    return response.json(), response_headers
                else:
                    return response.text, response_headers

            except httpx.HTTPStatusError as e:
                raise self.handle_http_status_error(e)
            except httpx.HTTPError as e:
                raise self.handle_http_error(e)

    async def verify_access(self) -> bool:
        """Verify that the token has access to the Gitea API."""
        try:
            await self.get_user()
            return True
        except Exception:
            return False

    async def get_user(self) -> User:
        """Get the authenticated user's information."""
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        return User(
            id=str(response['id']),
            login=response['login'],
            avatar_url=response['avatar_url'],
            company=response.get('company'),
            name=response.get('full_name'),
            email=response.get('email'),
        )

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str, public: bool
    ) -> list[Repository]:
        """Search for repositories."""
        url = f'{self.BASE_URL}/repos/search'
        params = {
            'q': query,
            'limit': per_page,
            'sort': sort,
            'order': order,
        }

        if public:
            params['private'] = 'false'

        response, _ = await self._make_request(url, params)
        repositories = []

        for repo in response.get('data', []):
            repositories.append(self._convert_to_repository(repo))

        return repositories

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        """Get all repositories for the authenticated user."""
        url = f'{self.BASE_URL}/user/repos'
        params = {
            'sort': sort,
            'limit': 100,  # Gitea's max per page
        }

        response, _ = await self._make_request(url, params)
        repositories = []

        for repo in response:
            repositories.append(self._convert_to_repository(repo))

        return repositories

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get a page of repositories."""
        url = f'{self.BASE_URL}/user/repos'
        params = {
            'page': page,
            'limit': per_page,
            'sort': sort,
        }

        response, _ = await self._make_request(url, params)
        repositories = []

        for repo in response:
            repositories.append(self._convert_to_repository(repo))

        return repositories

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user."""
        # Get user's repositories first
        repositories = await self.get_all_repositories('updated', AppMode.SAAS)
        tasks = []

        # For each repository, check for open issues and PRs
        for repo in repositories[:10]:  # Limit to first 10 repos for performance
            try:
                # Get open issues
                issues_url = f'{self.BASE_URL}/repos/{repo.full_name}/issues'
                issues_params = {'state': 'open', 'type': 'issues', 'limit': 5}
                issues_response, _ = await self._make_request(issues_url, issues_params)

                for issue in issues_response:
                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.GITEA,
                            task_type=TaskType.OPEN_ISSUE,
                            repo=repo.full_name,
                            issue_number=issue['number'],
                            title=issue['title'],
                        )
                    )

                # Get open PRs
                prs_url = f'{self.BASE_URL}/repos/{repo.full_name}/pulls'
                prs_params = {'state': 'open', 'limit': 5}
                prs_response, _ = await self._make_request(prs_url, prs_params)

                for pr in prs_response:
                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.GITEA,
                            task_type=TaskType.OPEN_PR,
                            repo=repo.full_name,
                            issue_number=pr['number'],
                            title=pr['title'],
                        )
                    )

            except Exception as e:
                logger.warning(f'Error fetching tasks for {repo.full_name}: {e}')
                continue

        return tasks

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Get repository details from repository name."""
        url = f'{self.BASE_URL}/repos/{repository}'
        response, _ = await self._make_request(url)
        return self._convert_to_repository(response)

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository."""
        url = f'{self.BASE_URL}/repos/{repository}/branches'
        response, _ = await self._make_request(url)

        branches = []
        for branch in response:
            branches.append(
                Branch(
                    name=branch['name'],
                    commit_sha=branch['commit']['id'],
                    protected=branch.get('protected', False),
                    last_push_date=branch['commit'].get('timestamp'),
                )
            )

        return branches

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Get content of a specific microagent file."""
        url = f'{self.BASE_URL}/repos/{repository}/contents/{file_path}'
        response, _ = await self._make_request(url)

        # Decode base64 content
        content = base64.b64decode(response['content']).decode('utf-8')

        # Parse the microagent content
        return self._parse_microagent_content(content, file_path)

    def _convert_to_repository(self, repo_data: dict) -> Repository:
        """Convert Gitea repository data to Repository object."""
        return Repository(
            id=str(repo_data['id']),
            full_name=repo_data['full_name'],
            git_provider=ProviderType.GITEA,
            is_public=not repo_data.get('private', False),
            stargazers_count=repo_data.get('stars_count', 0),
            pushed_at=repo_data.get('updated_at'),
            owner_type=OwnerType.ORGANIZATION
            if repo_data.get('owner', {}).get('type') == 'Organization'
            else OwnerType.USER,
            main_branch=repo_data.get('default_branch', 'main'),
        )


# Create the implementation class that will be used by the provider handler
class GiteaServiceImpl(GiteaService):
    """Implementation class for Gitea service."""

    pass
