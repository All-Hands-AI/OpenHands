import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.queries import (
    suggested_task_issue_graphql_query,
    suggested_task_pr_graphql_query,
)
from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    GitService,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    TaskType,
    UnknownException,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class GitHubService(BaseGitService, GitService):
    BASE_URL = 'https://api.github.com'
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

        if base_domain and base_domain != 'github.com':
            self.BASE_URL = f'https://{base_domain}/api/v3'

        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token

    def _find_git_repositories(self, base_dir: str) -> list[Repository]:
        """
        Find git repositories in the given directory and one level deep.

        Args:
            base_dir: The base directory to search for git repositories

        Returns:
            A list of Repository objects for git repositories found
        """
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            logger.warning(
                f'WORKSPACE_BASE directory does not exist or is not a directory: {base_dir}'
            )
            return []

        repositories = []
        base_path = Path(base_dir)

        # Check if the base directory itself is a git repository
        if (base_path / '.git').is_dir():
            repo = self._create_repository_from_local_git(base_path)
            if repo:
                repositories.append(repo)

        # Check one level deep
        for item in base_path.iterdir():
            if item.is_dir():
                # Check if this directory is a git repository
                if (item / '.git').is_dir():
                    repo = self._create_repository_from_local_git(item)
                    if repo:
                        repositories.append(repo)

        return repositories

    def _create_repository_from_local_git(self, repo_path: Path) -> Repository | None:
        """
        Create a Repository object from a local git repository.

        Args:
            repo_path: Path to the git repository

        Returns:
            A Repository object or None if the repository information cannot be extracted
        """
        try:
            # Get repository name from directory name
            repo_name = repo_path.name

            # Try to get the remote URL to extract the full name
            try:
                result = subprocess.run(
                    [
                        'git',
                        '-C',
                        str(repo_path),
                        'config',
                        '--get',
                        'remote.origin.url',
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                remote_url = result.stdout.strip()

                # Extract full name from remote URL if possible
                if remote_url:
                    # Handle different URL formats
                    if remote_url.startswith('https://'):
                        # Format: https://github.com/username/repo.git
                        parts = remote_url.split('/')
                        if len(parts) >= 5:
                            owner = parts[-2]
                            repo = parts[-1]
                            if repo.endswith('.git'):
                                repo = repo[:-4]
                            full_name = f'{owner}/{repo}'
                        else:
                            full_name = f'local/{repo_name}'
                    elif remote_url.startswith('git@'):
                        # Format: git@github.com:username/repo.git
                        parts = remote_url.split(':')
                        if len(parts) == 2:
                            repo_part = parts[1]
                            if repo_part.endswith('.git'):
                                repo_part = repo_part[:-4]
                            full_name = repo_part
                        else:
                            full_name = f'local/{repo_name}'
                    else:
                        full_name = f'local/{repo_name}'
                else:
                    full_name = f'local/{repo_name}'

            except Exception as e:
                logger.warning(
                    f'Error getting remote URL for repository {repo_path}: {e}'
                )
                full_name = f'local/{repo_name}'

            # Create a unique ID for the repository
            repo_id = hash(str(repo_path.absolute()))

            # Create the Repository object
            return Repository(
                id=abs(repo_id),  # Use absolute value to ensure positive ID
                full_name=full_name,
                git_provider=ProviderType.GITHUB,
                is_public=False,  # Assume local repositories are private
                stargazers_count=0,
                pushed_at=None,
            )

        except Exception as e:
            logger.warning(f'Error creating repository object for {repo_path}: {e}')
            return None

    @property
    def provider(self) -> str:
        return ProviderType.GITHUB.value

    async def _get_github_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def _has_token_expired(self, status_code: int) -> bool:
        return status_code == 401

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_github_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=github_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    github_headers = await self._get_github_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=github_headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        return User(
            id=response.get('id'),
            login=response.get('login'),
            avatar_url=response.get('avatar_url'),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )

    async def verify_access(self) -> bool:
        """Verify if the token is valid by making a simple request."""
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True

    async def _fetch_paginated_repos(
        self, url: str, params: dict, max_repos: int, extract_key: str | None = None
    ) -> list[dict]:
        """
        Fetch repositories with pagination support.

        Args:
            url: The API endpoint URL
            params: Query parameters for the request
            max_repos: Maximum number of repositories to fetch
            extract_key: If provided, extract repositories from this key in the response

        Returns:
            List of repository dictionaries
        """
        repos: list[dict] = []
        page = 1

        while len(repos) < max_repos:
            page_params = {**params, 'page': str(page)}
            response, headers = await self._make_request(url, page_params)

            # Extract repositories from response
            page_repos = response.get(extract_key, []) if extract_key else response

            if not page_repos:  # No more repositories
                break

            repos.extend(page_repos)
            page += 1

            # Check if we've reached the last page
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        return repos[:max_repos]  # Trim to max_repos if needed

    def parse_pushed_at_date(self, repo):
        ts = repo.get('pushed_at')
        return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ') if ts else datetime.min

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by GitHub API
        all_repos: list[dict] = []

        if app_mode == AppMode.SAAS:
            # Get all installation IDs and fetch repos for each one
            installation_ids = await self.get_installation_ids()

            # Iterate through each installation ID
            for installation_id in installation_ids:
                params = {'per_page': str(PER_PAGE)}
                url = (
                    f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
                )

                # Fetch repositories for this installation
                installation_repos = await self._fetch_paginated_repos(
                    url, params, MAX_REPOS - len(all_repos), extract_key='repositories'
                )

                all_repos.extend(installation_repos)

                # If we've already reached MAX_REPOS, no need to check other installations
                if len(all_repos) >= MAX_REPOS:
                    break

            if sort == 'pushed':
                all_repos.sort(key=self.parse_pushed_at_date, reverse=True)
        else:
            # Original behavior for non-SaaS mode
            params = {'per_page': str(PER_PAGE), 'sort': sort}
            url = f'{self.BASE_URL}/user/repos'

            # Fetch user repositories
            all_repos = await self._fetch_paginated_repos(url, params, MAX_REPOS)

        # Convert to Repository objects
        github_repos = [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
                git_provider=ProviderType.GITHUB,
                is_public=not repo.get('private', True),
            )
            for repo in all_repos
        ]

        # Check for local git repositories in WORKSPACE_BASE if the environment variable is set
        workspace_base = os.environ.get('WORKSPACE_BASE')
        local_repos = []

        if workspace_base:
            logger.info(
                f'Looking for git repositories in WORKSPACE_BASE: {workspace_base}'
            )
            local_repos = self._find_git_repositories(workspace_base)
            if local_repos:
                logger.info(
                    f'Found {len(local_repos)} local git repositories in WORKSPACE_BASE'
                )

        # Combine GitHub repositories and local repositories
        return github_repos + local_repos

    async def get_installation_ids(self) -> list[int]:
        url = f'{self.BASE_URL}/user/installations'
        response, _ = await self._make_request(url)
        installations = response.get('installations', [])
        return [i['id'] for i in installations]

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ) -> list[Repository]:
        url = f'{self.BASE_URL}/search/repositories'
        # Add is:public to the query to ensure we only search for public repositories
        query_with_visibility = f'{query} is:public'
        params = {
            'q': query_with_visibility,
            'per_page': per_page,
            'sort': sort,
            'order': order,
        }

        response, _ = await self._make_request(url, params)
        repo_items = response.get('items', [])

        repos = [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
                git_provider=ProviderType.GITHUB,
                is_public=True,
            )
            for repo in repo_items
        ]

        return repos

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API."""
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_github_headers()
                response = await client.post(
                    f'{self.BASE_URL}/graphql',
                    headers=github_headers,
                    json={'query': query, 'variables': variables},
                )
                response.raise_for_status()

                result = response.json()
                if 'errors' in result:
                    raise UnknownException(
                        f'GraphQL query error: {json.dumps(result["errors"])}'
                    )

                return dict(result)

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories.

        Returns:
        - PRs authored by the user.
        - Issues assigned to the user.

        Note: Queries are split to avoid timeout issues.
        """
        # Get user info to use in queries
        user = await self.get_user()
        login = user.login
        tasks: list[SuggestedTask] = []
        variables = {'login': login}

        try:
            pr_response = await self.execute_graphql_query(
                suggested_task_pr_graphql_query, variables
            )
            pr_data = pr_response['data']['user']

            # Process pull requests
            for pr in pr_data['pullRequests']['nodes']:
                repo_name = pr['repository']['nameWithOwner']

                # Start with default task type
                task_type = TaskType.OPEN_PR

                # Check for specific states
                if pr['mergeable'] == 'CONFLICTING':
                    task_type = TaskType.MERGE_CONFLICTS
                elif (
                    pr['commits']['nodes']
                    and pr['commits']['nodes'][0]['commit']['statusCheckRollup']
                    and pr['commits']['nodes'][0]['commit']['statusCheckRollup'][
                        'state'
                    ]
                    == 'FAILURE'
                ):
                    task_type = TaskType.FAILING_CHECKS
                elif any(
                    review['state'] in ['CHANGES_REQUESTED', 'COMMENTED']
                    for review in pr['reviews']['nodes']
                ):
                    task_type = TaskType.UNRESOLVED_COMMENTS

                # Only add the task if it's not OPEN_PR
                if task_type != TaskType.OPEN_PR:
                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.GITHUB,
                            task_type=task_type,
                            repo=repo_name,
                            issue_number=pr['number'],
                            title=pr['title'],
                        )
                    )

        except Exception as e:
            logger.info(
                f'Error fetching suggested task for PRs: {e}',
                extra={
                    'signal': 'github_suggested_tasks',
                    'user_id': self.external_auth_id,
                },
            )

        try:
            # Execute issue query
            issue_response = await self.execute_graphql_query(
                suggested_task_issue_graphql_query, variables
            )
            issue_data = issue_response['data']['user']

            # Process issues
            for issue in issue_data['issues']['nodes']:
                repo_name = issue['repository']['nameWithOwner']
                tasks.append(
                    SuggestedTask(
                        git_provider=ProviderType.GITHUB,
                        task_type=TaskType.OPEN_ISSUE,
                        repo=repo_name,
                        issue_number=issue['number'],
                        title=issue['title'],
                    )
                )

            return tasks

        except Exception as e:
            logger.info(
                f'Error fetching suggested task for issues: {e}',
                extra={
                    'signal': 'github_suggested_tasks',
                    'user_id': self.external_auth_id,
                },
            )

        return tasks

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        url = f'{self.BASE_URL}/repos/{repository}'
        repo, _ = await self._make_request(url)

        return Repository(
            id=repo.get('id'),
            full_name=repo.get('full_name'),
            stargazers_count=repo.get('stargazers_count'),
            git_provider=ProviderType.GITHUB,
            is_public=not repo.get('private', True),
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""
        url = f'{self.BASE_URL}/repos/{repository}/branches'

        # Set maximum branches to fetch (10 pages with 100 per page)
        MAX_BRANCHES = 1000
        PER_PAGE = 100

        all_branches: list[Branch] = []
        page = 1

        # Fetch up to 10 pages of branches
        while page <= 10 and len(all_branches) < MAX_BRANCHES:
            params = {'per_page': str(PER_PAGE), 'page': str(page)}
            response, headers = await self._make_request(url, params)

            if not response:  # No more branches
                break

            for branch_data in response:
                # Extract the last commit date if available
                last_push_date = None
                if branch_data.get('commit') and branch_data['commit'].get('commit'):
                    commit_info = branch_data['commit']['commit']
                    if commit_info.get('committer') and commit_info['committer'].get(
                        'date'
                    ):
                        last_push_date = commit_info['committer']['date']

                branch = Branch(
                    name=branch_data.get('name'),
                    commit_sha=branch_data.get('commit', {}).get('sha', ''),
                    protected=branch_data.get('protected', False),
                    last_push_date=last_push_date,
                )
                all_branches.append(branch)

            page += 1

            # Check if we've reached the last page
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        return all_branches


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
