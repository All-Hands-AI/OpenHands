import base64
import json
import os
from datetime import datetime
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.github.queries import (
    get_review_threads_graphql_query,
    get_thread_comments_graphql_query,
    get_thread_from_comment_graphql_query,
    search_branches_graphql_query,
    suggested_task_issue_graphql_query,
    suggested_task_pr_graphql_query,
)
from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    Comment,
    GitService,
    InstallationsService,
    OwnerType,
    PaginatedBranchesResponse,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    TaskType,
    UnknownException,
    User,
)
from openhands.microagent.types import MicroagentContentResponse
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class GitHubService(BaseGitService, GitService, InstallationsService):
    """Default implementation of GitService for GitHub integration.

    TODO: This doesn't seem a good candidate for the get_impl() pattern. What are the abstract methods we should actually separate and implement here?
    This is an extension point in OpenHands that allows applications to customize GitHub
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.github_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

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

    @property
    def provider(self) -> str:
        return ProviderType.GITHUB.value

    async def _get_github_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
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

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return (
            item['type'] == 'file'
            and item['name'].endswith('.md')
            and item['name'] != 'README.md'
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        return item['name']

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return f'{microagents_path}/{item["name"]}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request. Return None if no parameters needed."""
        return None

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
            id=str(response.get('id', '')),
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
        """Fetch repositories with pagination support.

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

    def _parse_repository(
        self, repo: dict, link_header: str | None = None
    ) -> Repository:
        """Parse a GitHub API repository response into a Repository object.

        Args:
            repo: Repository data from GitHub API
            link_header: Optional link header for pagination

        Returns:
            Repository object
        """
        return Repository(
            id=str(repo.get('id')),  # type: ignore[arg-type]
            full_name=repo.get('full_name'),  # type: ignore[arg-type]
            stargazers_count=repo.get('stargazers_count'),
            git_provider=ProviderType.GITHUB,
            is_public=not repo.get('private', True),
            owner_type=(
                OwnerType.ORGANIZATION
                if repo.get('owner', {}).get('type') == 'Organization'
                else OwnerType.USER
            ),
            link_header=link_header,
            main_branch=repo.get('default_branch'),
        )

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ):
        params = {'page': str(page), 'per_page': str(per_page)}
        if installation_id:
            url = f'{self.BASE_URL}/user/installations/{installation_id}/repositories'
            response, headers = await self._make_request(url, params)
            response = response.get('repositories', [])
        else:
            url = f'{self.BASE_URL}/user/repos'
            params['sort'] = sort
            response, headers = await self._make_request(url, params)

        next_link: str = headers.get('Link', '')
        return [
            self._parse_repository(repo, link_header=next_link) for repo in response
        ]

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by GitHub API
        all_repos: list[dict] = []

        if app_mode == AppMode.SAAS:
            # Get all installation IDs and fetch repos for each one
            installation_ids = await self.get_installations()

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
        return [self._parse_repository(repo) for repo in all_repos]

    async def get_installations(self) -> list[str]:
        url = f'{self.BASE_URL}/user/installations'
        response, _ = await self._make_request(url)
        installations = response.get('installations', [])
        return [str(i['id']) for i in installations]

    async def get_user_organizations(self) -> list[str]:
        """Get list of organization logins that the user is a member of."""
        url = f'{self.BASE_URL}/user/orgs'
        try:
            response, _ = await self._make_request(url)
            orgs = [org['login'] for org in response]
            return orgs
        except Exception as e:
            logger.warning(f'Failed to get user organizations: {e}')
            return []

    def _fuzzy_match_org_name(self, query: str, org_name: str) -> bool:
        """Check if query fuzzy matches organization name."""
        query_lower = query.lower().replace('-', '').replace('_', '').replace(' ', '')
        org_lower = org_name.lower().replace('-', '').replace('_', '').replace(' ', '')

        # Exact match after normalization
        if query_lower == org_lower:
            return True

        # Query is a substring of org name
        if query_lower in org_lower:
            return True

        # Org name is a substring of query (less common but possible)
        if org_lower in query_lower:
            return True

        return False

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str, public: bool
    ) -> list[Repository]:
        url = f'{self.BASE_URL}/search/repositories'
        params = {
            'per_page': per_page,
            'sort': sort,
            'order': order,
        }

        if public:
            url_parts = query.split('/')
            if len(url_parts) < 4:
                return []

            org = url_parts[3]
            repo_name = url_parts[4]
            # Add is:public to the query to ensure we only search for public repositories
            params['q'] = f'in:name {org}/{repo_name} is:public'

        # Handle private repository searches
        if not public and '/' in query:
            org, repo_query = query.split('/', 1)
            query_with_user = f'org:{org} in:name {repo_query}'
            params['q'] = query_with_user
        elif not public:
            # Expand search scope to include user's repositories and organizations they're a member of
            user = await self.get_user()
            user_orgs = await self.get_user_organizations()

            # Search in user repos and org repos separately
            all_repos = []

            # Search in user repositories
            user_query = f'{query} user:{user.login}'
            user_params = params.copy()
            user_params['q'] = user_query

            try:
                user_response, _ = await self._make_request(url, user_params)
                user_items = user_response.get('items', [])
                all_repos.extend(user_items)
            except Exception as e:
                logger.warning(f'User search failed: {e}')

            # Search for repos named "query" in each organization
            for org in user_orgs:
                org_query = f'{query} org:{org}'
                org_params = params.copy()
                org_params['q'] = org_query

                try:
                    org_response, _ = await self._make_request(url, org_params)
                    org_items = org_response.get('items', [])
                    all_repos.extend(org_items)
                except Exception as e:
                    logger.warning(f'Org {org} search failed: {e}')

            # Also search for top repos from orgs that match the query name
            for org in user_orgs:
                if self._fuzzy_match_org_name(query, org):
                    org_repos_query = f'org:{org}'
                    org_repos_params = params.copy()
                    org_repos_params['q'] = org_repos_query
                    org_repos_params['sort'] = 'stars'
                    org_repos_params['per_page'] = 2  # Limit to first 2 repos

                    try:
                        org_repos_response, _ = await self._make_request(
                            url, org_repos_params
                        )
                        org_repo_items = org_repos_response.get('items', [])
                        all_repos.extend(org_repo_items)
                    except Exception as e:
                        logger.warning(f'Org repos search for {org} failed: {e}')

            return [self._parse_repository(repo) for repo in all_repos]

        # Default case (public search or slash query)
        response, _ = await self._make_request(url, params)
        repo_items = response.get('items', [])
        return [self._parse_repository(repo) for repo in repo_items]

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

        return self._parse_repository(repo)

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""
        url = f'{self.BASE_URL}/repos/{repository}/branches'

        # Set maximum branches to fetch (100 per page)
        MAX_BRANCHES = 5_000
        PER_PAGE = 100

        all_branches: list[Branch] = []
        page = 1

        # Fetch up to 10 pages of branches
        while len(all_branches) < MAX_BRANCHES:
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

    async def get_paginated_branches(
        self, repository: str, page: int = 1, per_page: int = 30
    ) -> PaginatedBranchesResponse:
        """Get branches for a repository with pagination"""
        url = f'{self.BASE_URL}/repos/{repository}/branches'

        params = {'per_page': str(per_page), 'page': str(page)}
        response, headers = await self._make_request(url, params)

        branches: list[Branch] = []
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
            branches.append(branch)

        # Parse Link header to determine if there's a next page
        has_next_page = False
        if 'Link' in headers:
            link_header = headers['Link']
            has_next_page = 'rel="next"' in link_header

        return PaginatedBranchesResponse(
            branches=branches,
            has_next_page=has_next_page,
            current_page=page,
            per_page=per_page,
            total_count=None,  # GitHub doesn't provide total count in branch API
        )

    async def search_branches(
        self, repository: str, query: str, per_page: int = 30
    ) -> list[Branch]:
        """Search branches by name using GitHub GraphQL with a partial query."""
        # Require a non-empty query
        if not query:
            return []

        # Clamp per_page to GitHub GraphQL limits
        per_page = min(max(per_page, 1), 100)

        # Extract owner and repo name from the repository string
        parts = repository.split('/')
        if len(parts) < 2:
            return []
        owner, name = parts[-2], parts[-1]

        variables = {
            'owner': owner,
            'name': name,
            'query': query or '',
            'perPage': per_page,
        }

        try:
            result = await self.execute_graphql_query(
                search_branches_graphql_query, variables
            )
        except Exception as e:
            logger.warning(f'Failed to search for branches: {e}')
            # Fallback to empty result on any GraphQL error
            return []

        repo = result.get('data', {}).get('repository')
        if not repo or not repo.get('refs'):
            return []

        branches: list[Branch] = []
        for node in repo['refs'].get('nodes', []):
            bname = node.get('name') or ''
            target = node.get('target') or {}
            typename = target.get('__typename')
            commit_sha = ''
            last_push_date = None
            if typename == 'Commit':
                commit_sha = target.get('oid', '') or ''
                last_push_date = target.get('committedDate')

            protected = node.get('branchProtectionRule') is not None

            branches.append(
                Branch(
                    name=bname,
                    commit_sha=commit_sha,
                    protected=protected,
                    last_push_date=last_push_date,
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
        draft: bool = True,
        labels: list[str] | None = None,
    ) -> str:
        """Creates a PR using user credentials

        Args:
            repo_name: The full name of the repository (owner/repo)
            source_branch: The name of the branch where your changes are implemented
            target_branch: The name of the branch you want the changes pulled into
            title: The title of the pull request (optional, defaults to a generic title)
            body: The body/description of the pull request (optional)
            draft: Whether to create the PR as a draft (optional, defaults to False)
            labels: A list of labels to apply to the pull request (optional)

        Returns:
            - PR URL when successful
            - Error message when unsuccessful
        """
        url = f'{self.BASE_URL}/repos/{repo_name}/pulls'

        # Set default body if none provided
        if not body:
            body = f'Merging changes from {source_branch} into {target_branch}'

        # Prepare the request payload
        payload = {
            'title': title,
            'head': source_branch,
            'base': target_branch,
            'body': body,
            'draft': draft,
        }

        # Make the POST request to create the PR
        response, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        # Add labels if provided (PRs are a type of issue in GitHub's API)
        if labels and len(labels) > 0:
            pr_number = response['number']
            labels_url = f'{self.BASE_URL}/repos/{repo_name}/issues/{pr_number}/labels'
            labels_payload = {'labels': labels}
            await self._make_request(
                url=labels_url, params=labels_payload, method=RequestMethod.POST
            )

        # Return the HTML URL of the created PR
        return response['html_url']

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:
        """Get detailed information about a specific pull request

        Args:
            repository: Repository name in format 'owner/repo'
            pr_number: The pull request number

        Returns:
            Raw GitHub API response for the pull request
        """
        url = f'{self.BASE_URL}/repos/{repository}/pulls/{pr_number}'
        pr_data, _ = await self._make_request(url)

        return pr_data

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Fetch individual file content from GitHub repository.

        Args:
            repository: Repository name in format 'owner/repo'
            file_path: Path to the file within the repository

        Returns:
            MicroagentContentResponse with parsed content and triggers

        Raises:
            RuntimeError: If file cannot be fetched or doesn't exist
        """
        file_url = f'{self.BASE_URL}/repos/{repository}/contents/{file_path}'

        file_data, _ = await self._make_request(file_url)
        file_content = base64.b64decode(file_data['content']).decode('utf-8')

        # Parse the content to extract triggers from frontmatter
        return self._parse_microagent_content(file_content, file_path)

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:
        """Check if a GitHub PR is still active (not closed/merged).

        Args:
            repository: Repository name in format 'owner/repo'
            pr_number: The PR number to check

        Returns:
            True if PR is active (open), False if closed/merged
        """
        try:
            pr_details = await self.get_pr_details(repository, pr_number)

            # GitHub API response structure
            # https://docs.github.com/en/rest/pulls/pulls#get-a-pull-request
            if 'state' in pr_details:
                return pr_details['state'] == 'open'
            elif 'merged' in pr_details and 'closed_at' in pr_details:
                # Check if PR is merged or closed
                return not (pr_details['merged'] or pr_details['closed_at'])

            # If we can't determine the state, assume it's active (safer default)
            logger.warning(
                f'Could not determine GitHub PR status for {repository}#{pr_number}. '
                f'Response keys: {list(pr_details.keys())}. Assuming PR is active.'
            )
            return True

        except Exception as e:
            logger.warning(
                f'Could not determine GitHub PR status for {repository}#{pr_number}: {e}. '
                f'Including conversation to be safe.'
            )
            # If we can't determine the PR status, include the conversation to be safe
            return True

    async def get_issue_or_pr_comments(
        self, repository: str, issue_number: int, max_comments: int = 10
    ) -> list[Comment]:
        """Get comments for an issue.

        Args:
            repository: Repository name in format 'owner/repo'
            issue_number: The issue number
            discussion_id: Not used for GitHub (kept for compatibility with GitLab)

        Returns:
            List of Comment objects ordered by creation date
        """
        url = f'{self.BASE_URL}/repos/{repository}/issues/{issue_number}/comments'
        page = 1
        all_comments: list[dict] = []

        while len(all_comments) < max_comments:
            params = {
                'per_page': 10,
                'sort': 'created',
                'direction': 'asc',
                'page': page,
            }
            response, headers = await self._make_request(url, params=params)
            all_comments.extend(response or [])

            # Parse the Link header for rel="next"
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

            page += 1

        return self._process_raw_comments(all_comments)

    async def get_issue_or_pr_title_and_body(
        self, repository: str, issue_number: int
    ) -> tuple[str, str]:
        """Get the title and body of an issue.

        Args:
            repository: Repository name in format 'owner/repo'
            issue_number: The issue number

        Returns:
            A tuple of (title, body)
        """
        url = f'{self.BASE_URL}/repos/{repository}/issues/{issue_number}'
        response, _ = await self._make_request(url)
        title = response.get('title') or ''
        body = response.get('body') or ''
        return title, body

    async def get_review_thread_comments(
        self,
        comment_id: str,
        repository: str,
        pr_number: int,
    ) -> list[Comment]:
        """Get all comments in a review thread starting from a specific comment.

        Uses GraphQL to traverse the reply chain from the given comment up to the root
        comment, then finds the review thread and returns all comments in the thread.

        Args:
            comment_id: The GraphQL node ID of any comment in the thread
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of Comment objects representing the entire thread
        """

        # Step 1: Use existing GraphQL query to get the comment and check for replyTo
        variables = {'commentId': comment_id}
        data = await self.execute_graphql_query(
            get_thread_from_comment_graphql_query, variables
        )

        comment_node = data.get('data', {}).get('node')
        if not comment_node:
            return []

        # Step 2: If replyTo exists, traverse to the root comment
        root_comment_id = comment_id
        reply_to = comment_node.get('replyTo')
        if reply_to:
            root_comment_id = reply_to['id']

        # Step 3: Get all review threads and find the one containing our root comment
        owner, repo = repository.split('/')
        thread_id = None
        after_cursor = None
        has_next_page = True

        while has_next_page and not thread_id:
            threads_variables: dict[str, Any] = {
                'owner': owner,
                'repo': repo,
                'number': pr_number,
                'first': 50,
            }
            if after_cursor:
                threads_variables['after'] = after_cursor

            threads_data = await self.execute_graphql_query(
                get_review_threads_graphql_query, threads_variables
            )

            review_threads_data = (
                threads_data.get('data', {})
                .get('repository', {})
                .get('pullRequest', {})
                .get('reviewThreads', {})
            )

            review_threads = review_threads_data.get('nodes', [])
            page_info = review_threads_data.get('pageInfo', {})

            # Search for the thread containing our root comment
            for thread in review_threads:
                first_comments = thread.get('comments', {}).get('nodes', [])
                for first_comment in first_comments:
                    if first_comment.get('id') == root_comment_id:
                        thread_id = thread.get('id')
                        break
                if thread_id:
                    break

            # Update pagination variables
            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')

        if not thread_id:
            # Fallback: return just the comments we found during traversal
            logger.warning(
                f'Could not find review thread for comment {comment_id}, returning traversed comments'
            )
            return []

        # Step 4: Get all comments from the review thread using the thread ID
        all_thread_comments = []
        after_cursor = None
        has_next_page = True

        while has_next_page:
            comments_variables: dict[str, Any] = {}
            comments_variables['threadId'] = thread_id
            comments_variables['page'] = 50
            if after_cursor:
                comments_variables['after'] = after_cursor

            thread_comments_data = await self.execute_graphql_query(
                get_thread_comments_graphql_query, comments_variables
            )

            thread_node = thread_comments_data.get('data', {}).get('node')
            if not thread_node:
                break

            comments_data = thread_node.get('comments', {})
            comments_nodes = comments_data.get('nodes', [])
            page_info = comments_data.get('pageInfo', {})

            all_thread_comments.extend(comments_nodes)

            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')

        return self._process_raw_comments(all_thread_comments)

    def _process_raw_comments(
        self, comments_data: list, max_comments: int = 10
    ) -> list[Comment]:
        """Convert raw comment data to Comment objects."""
        comments: list[Comment] = []
        for comment in comments_data:
            author = 'unknown'

            if comment.get('author'):
                author = comment.get('author', {}).get('login', 'unknown')
            elif comment.get('user'):
                author = comment.get('user', {}).get('login', 'unknown')

            comments.append(
                Comment(
                    id=str(comment.get('id', 'unknown')),
                    body=self._truncate_comment(comment.get('body', '')),
                    author=author,
                    created_at=datetime.fromisoformat(
                        comment.get('createdAt', '').replace('Z', '+00:00')
                    )
                    if comment.get('createdAt')
                    else datetime.fromtimestamp(0),
                    updated_at=datetime.fromisoformat(
                        comment.get('updatedAt', '').replace('Z', '+00:00')
                    )
                    if comment.get('updatedAt')
                    else datetime.fromtimestamp(0),
                    system=False,
                )
            )

        # Sort comments by creation date to maintain chronological order
        comments.sort(key=lambda c: c.created_at)
        return comments[-max_comments:]


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
