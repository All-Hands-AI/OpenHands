import os
import json
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.github.github_types import (
    GhAuthenticationError,
    GHUnknownException,
    GitHubRepository,
    GitHubUser,
    TaskType,
    SuggestedTask,
)
from openhands.utils.import_utils import get_impl


class GitHubService:
    BASE_URL = 'https://api.github.com'
    token: SecretStr = SecretStr('')
    refresh = False

    def __init__(self, user_id: str | None = None, token: SecretStr | None = None):
        self.user_id = user_id

        if token:
            self.token = token

    async def _get_github_headers(self) -> dict:
        """
        Retrieve the GH Token from settings store to construct the headers
        """

        if self.user_id and not self.token:
            self.token = await self.get_latest_token()

        return {
            'Authorization': f'Bearer {self.token.get_secret_value()}',
            'Accept': 'application/vnd.github.v3+json',
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
                raise GhAuthenticationError('Invalid Github token')
            raise GHUnknownException('Unknown error')

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

    async def execute_graphql_query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API."""
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_github_headers()
                response = await client.post(
                    f"{self.BASE_URL}/graphql",
                    headers=github_headers,
                    json={"query": query, "variables": variables}
                )
                response.raise_for_status()
                
                result = response.json()
                if "errors" in result:
                    raise GHUnknownException(f"GraphQL query error: {json.dumps(result['errors'])}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GhAuthenticationError('Invalid Github token')
            raise GHUnknownException('Unknown error')

        except httpx.HTTPError:
            raise GHUnknownException('Unknown error')

    async def get_suggested_tasks(self, repo_full_name: str) -> list[SuggestedTask]:
        """
        Get suggested tasks for a repository, including:
        - PRs with merge conflicts
        - PRs with failing GitHub Actions
        - PRs with unresolved comments
        - Issues with specific labels (help wanted, chore, documentation, good first issue)
        """
        query = """
        query GetSuggestedTasks($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            pullRequests(first: 100, states: [OPEN]) {
              nodes {
                number
                title
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
            issues(first: 100, states: [OPEN], labels: ["help wanted", "chore", "documentation", "good first issue"]) {
              nodes {
                number
                title
                labels(first: 10) {
                  nodes {
                    name
                  }
                }
              }
            }
          }
        }
        """

        owner, name = repo_full_name.split("/")
        variables = {
            "owner": owner,
            "name": name
        }

        response = await self.execute_graphql_query(query, variables)
        data = response["data"]["repository"]
        tasks: list[SuggestedTask] = []

        # Process pull requests
        for pr in data["pullRequests"]["nodes"]:
            # Check for merge conflicts
            if pr["mergeable"] == "CONFLICTING":
                tasks.append(SuggestedTask(
                    task_type=TaskType.MERGE_CONFLICTS,
                    repo=repo_full_name,
                    issue_number=pr["number"],
                    title=pr["title"]
                ))

            # Check for failing checks
            if pr["commits"]["nodes"] and pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"]:
                if pr["commits"]["nodes"][0]["commit"]["statusCheckRollup"]["state"] == "FAILURE":
                    tasks.append(SuggestedTask(
                        task_type=TaskType.FAILING_CHECKS,
                        repo=repo_full_name,
                        issue_number=pr["number"],
                        title=pr["title"]
                    ))

            # Check for unresolved comments
            has_unresolved_comments = any(
                review["state"] in ["CHANGES_REQUESTED", "COMMENTED"]
                for review in pr["reviews"]["nodes"]
            )
            if has_unresolved_comments:
                tasks.append(SuggestedTask(
                    task_type=TaskType.UNRESOLVED_COMMENTS,
                    repo=repo_full_name,
                    issue_number=pr["number"],
                    title=pr["title"]
                ))

        # Process issues
        for issue in data["issues"]["nodes"]:
            tasks.append(SuggestedTask(
                task_type=TaskType.OPEN_ISSUE,
                repo=repo_full_name,
                issue_number=issue["number"],
                title=issue["title"]
            ))

        return tasks


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
