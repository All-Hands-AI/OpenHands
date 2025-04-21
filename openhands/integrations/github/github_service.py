import json
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
    SuggestedTask,
    TaskType,
    UnknownException,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class GitHubService(GitService):
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
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

    async def _get_github_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
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
                github_headers = await self._get_github_headers()
                response = await client.get(url, headers=github_headers, params=params)
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    github_headers = await self._get_github_headers()
                    response = await client.get(
                        url, headers=github_headers, params=params
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid Github token')

            logger.warning(f'Status error on GH API: {e}')
            raise UnknownException('Unknown error')

        except httpx.HTTPError as e:
            logger.warning(f'HTTP error on GH API: {e}')
            raise UnknownException('Unknown error')

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._fetch_data(url)

        return User(
            id=response.get('id'),
            login=response.get('login'),
            avatar_url=response.get('avatar_url'),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )

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
            response, headers = await self._fetch_data(url, page_params)

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
        else:
            # Original behavior for non-SaaS mode
            params = {'per_page': str(PER_PAGE), 'sort': sort}
            url = f'{self.BASE_URL}/user/repos'

            # Fetch user repositories
            all_repos = await self._fetch_paginated_repos(url, params, MAX_REPOS)

        # Convert to Repository objects
        return [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
                git_provider=ProviderType.GITHUB,
                is_public=not repo.get('private', True),
            )
            for repo in all_repos
        ]

    async def get_installation_ids(self) -> list[int]:
        url = f'{self.BASE_URL}/user/installations'
        response, _ = await self._fetch_data(url)
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

        response, _ = await self._fetch_data(url, params)
        repo_items = response.get('items', [])

        repos = [
            Repository(
                id=repo.get('id'),
                full_name=repo.get('full_name'),
                stargazers_count=repo.get('stargazers_count'),
                git_provider=ProviderType.GITHUB,
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
                        f"GraphQL query error: {json.dumps(result['errors'])}"
                    )

                return dict(result)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError('Invalid Github token')

            logger.warning(f'Status error on GH API: {e}')
            raise UnknownException('Unknown error')

        except httpx.HTTPError as e:
            logger.warning(f'HTTP error on GH API: {e}')
            raise UnknownException('Unknown error')

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories.

        Returns:
        - PRs authored by the user.
        - Issues assigned to the user.
        """
        # Get user info to use in queries
        user = await self.get_user()
        login = user.login

        query = """
        query GetUserTasks($login: String!) {
          user(login: $login) {
            pullRequests(first: 100, states: [OPEN], orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                number
                title
                repository {
                  nameWithOwner
                }
                mergeable
                commits(last: 1) {
                  nodes {
                    commit {
                      statusCheckRollup {
                        state
                      }
                    }
                  }
                }
                reviews(first: 100, states: [CHANGES_REQUESTED, COMMENTED]) {
                  nodes {
                    state
                  }
                }
              }
            }
            issues(first: 100, states: [OPEN], filterBy: {assignee: $login}, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                number
                title
                repository {
                  nameWithOwner
                }
              }
            }
          }
        }
        """

        variables = {'login': login}

        try:
            response = await self.execute_graphql_query(query, variables)
            data = response['data']['user']
            tasks: list[SuggestedTask] = []

            # Process pull requests
            for pr in data['pullRequests']['nodes']:
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
                            task_type=task_type,
                            repo=repo_name,
                            issue_number=pr['number'],
                            title=pr['title'],
                        )
                    )

            # Process issues
            for issue in data['issues']['nodes']:
                repo_name = issue['repository']['nameWithOwner']
                tasks.append(
                    SuggestedTask(
                        task_type=TaskType.OPEN_ISSUE,
                        repo=repo_name,
                        issue_number=issue['number'],
                        title=issue['title'],
                    )
                )

            return tasks
        except Exception:
            return []


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
