"""
Azure DevOps service implementation using standard HTTP API calls.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    AuthenticationError,
    BaseGitService,
    Branch,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    TaskType,
    UnknownException,
    User,
)
from openhands.server.types import AppMode


class AzureDevOpsServiceImpl(BaseGitService):
    """Azure DevOps service implementation using standard HTTP API calls."""

    def __init__(
        self,
        user_id: str | None = None,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
        organization_url: str | None = None,
    ):
        """Initialize the Azure DevOps service.

        Args:
            user_id: The user ID
            token: The Azure DevOps personal access token
            external_auth_id: External auth ID (not used for Azure DevOps)
            external_auth_token: External auth token (not used for Azure DevOps)
            external_token_manager: Whether to use external token manager (not used for Azure DevOps)
            organization_url: The Azure DevOps organization URL (e.g., https://dev.azure.com/organization)
        """
        self.user_id = user_id
        self.token = token
        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.external_token_manager = external_token_manager
        self.organization_url = organization_url or 'https://dev.azure.com'

        # Extract organization name from URL for API calls
        if self.organization_url.startswith('https://dev.azure.com/'):
            self.organization = self.organization_url.replace(
                'https://dev.azure.com/', ''
            ).rstrip('/')
        else:
            # Handle custom Azure DevOps Server URLs
            self.organization = (
                self.organization_url.split('/')[-1]
                if '/' in self.organization_url
                else self.organization_url
            )

        self.base_url = f'https://dev.azure.com/{self.organization}/_apis'

    @property
    def provider(self) -> str:
        return ProviderType.AZURE_DEVOPS.value

    async def _get_azure_devops_headers(self) -> dict[str, str]:
        """Get headers for Azure DevOps API requests."""
        if not self.token:
            self.token = await self.get_latest_token()

        if not self.token:
            raise AuthenticationError('No Azure DevOps token provided')

        # Azure DevOps uses Basic authentication with PAT
        # Username can be empty, password is the PAT
        credentials = base64.b64encode(
            f':{self.token.get_secret_value()}'.encode()
        ).decode()

        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if the token has expired."""
        return status_code == 401

    async def execute_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ) -> httpx.Response:
        """Execute an HTTP request."""
        if method == RequestMethod.GET:
            response = await client.get(url, headers=headers, params=params)
        elif method == RequestMethod.POST:
            response = await client.post(url, headers=headers, json=params)
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')

        return response

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
        json_data: dict | None = None,
    ) -> tuple[Any, dict]:
        """Make a request to the Azure DevOps API."""
        try:
            async with httpx.AsyncClient() as client:
                azure_devops_headers = await self._get_azure_devops_headers()

                # Make initial request
                # For POST requests, use json_data as params (following base class pattern)
                request_params = json_data if method == RequestMethod.POST else params
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=azure_devops_headers,
                    params=request_params,
                    method=method,
                )

                # Handle token refresh if needed
                if self._has_token_expired(response.status_code):
                    logger.warning('Azure DevOps token expired, attempting refresh')
                    # For Azure DevOps, we don't have automatic token refresh
                    # The user needs to provide a new PAT
                    raise AuthenticationError(
                        'Azure DevOps token expired. Please provide a new Personal Access Token.'
                    )

                if response.status_code >= 400:
                    logger.error(
                        f'Azure DevOps API error: {response.status_code} - {response.text}'
                    )
                    if response.status_code == 401:
                        raise AuthenticationError(
                            'Authentication failed with Azure DevOps'
                        )
                    elif response.status_code == 403:
                        raise AuthenticationError(
                            'Access forbidden. Check your Azure DevOps permissions.'
                        )
                    elif response.status_code == 404:
                        raise ValueError('Resource not found')
                    else:
                        raise UnknownException(
                            f'Azure DevOps API error: {response.status_code}'
                        )

                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text

                return response_data, {}

        except httpx.RequestError as e:
            logger.error(f'Request error: {e}')
            raise UnknownException(f'Request failed: {e}')
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            raise UnknownException(f'Unexpected error: {e}')

    async def get_latest_token(self) -> SecretStr | None:
        """Get the latest token.

        Returns:
            The latest token
        """
        return self.token

    async def get_user(self) -> User:
        """Get the authenticated user.

        Returns:
            The authenticated user
        """
        try:
            # Try to get user profile from Azure DevOps
            # First, try to get the user's profile using the profile API
            profile_url = f'{self.base_url}/profile/profiles/me'
            profile_params = {'api-version': '7.1-preview.3'}

            try:
                profile_data, _ = await self._make_request(
                    profile_url, params=profile_params
                )

                if profile_data and isinstance(profile_data, dict):
                    return User(
                        id=profile_data.get('id', 0),
                        login=profile_data.get(
                            'emailAddress', self.user_id or 'azure_devops_user'
                        ),
                        avatar_url=profile_data.get('avatar', {}).get('value', ''),
                        name=profile_data.get(
                            'displayName', self.user_id or 'Azure DevOps User'
                        ),
                        email=profile_data.get('emailAddress'),
                        company=None,
                    )
            except Exception as profile_error:
                logger.warning(f'Could not get user profile: {profile_error}')

            # Fallback: Try to get projects to verify authentication
            projects_url = f'{self.base_url}/projects'
            projects_params = {'api-version': '7.1-preview.4'}

            projects_data, _ = await self._make_request(
                projects_url, params=projects_params
            )

            # If we can get projects, authentication is working
            if projects_data:
                return User(
                    id=0,  # Placeholder ID
                    login=self.user_id or 'azure_devops_user',
                    avatar_url='',
                    name=self.user_id or 'Azure DevOps User',
                    email=None,
                    company=None,
                )
            else:
                raise AuthenticationError('Failed to authenticate with Azure DevOps')

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f'Error getting Azure DevOps user: {e}')
            raise AuthenticationError(f'Failed to authenticate with Azure DevOps: {e}')

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user.

        Args:
            sort: The sort order
            app_mode: The app mode

        Returns:
            A list of repositories
        """
        try:
            # Get all repositories across all projects
            repos_url = f'{self.base_url}/git/repositories'
            repos_params = {'api-version': '7.1-preview.1'}

            repos_data, _ = await self._make_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                return []

            repositories = repos_data.get('value', [])

            # Convert to Repository objects
            result = []
            for repo in repositories:
                project_name = repo.get('project', {}).get('name', 'Unknown')
                repo_name = repo.get('name', 'Unknown')

                result.append(
                    Repository(
                        id=repo.get('id', ''),
                        full_name=f'{project_name}/{repo_name}',
                        git_provider=ProviderType.AZURE_DEVOPS,
                        is_public=False,  # Azure DevOps repos are private by default
                        stargazers_count=None,
                        link_header=None,
                        pushed_at=None,
                    )
                )

            return result
        except Exception as e:
            logger.error(f'Error getting Azure DevOps repositories: {e}')
            return []

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        """Search for repositories.

        Args:
            query: The search query
            per_page: The number of results per page
            sort: The sort order
            order: The sort direction

        Returns:
            A list of repositories
        """
        try:
            # Get all repositories (Azure DevOps doesn't have a search API for repos)
            repos_url = f'{self.base_url}/git/repositories'
            repos_params = {'api-version': '7.1-preview.1'}

            repos_data, _ = await self._make_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                return []

            repositories = repos_data.get('value', [])

            # Filter repositories by name (simple client-side filtering)
            filtered_repos = [
                repo
                for repo in repositories
                if query.lower() in repo.get('name', '').lower()
                or query.lower() in repo.get('project', {}).get('name', '').lower()
            ]

            # Convert to Repository objects
            result = []
            for repo in filtered_repos[:per_page]:
                project_name = repo.get('project', {}).get('name', 'Unknown')
                repo_name = repo.get('name', 'Unknown')

                result.append(
                    Repository(
                        id=repo.get('id', ''),
                        full_name=f'{project_name}/{repo_name}',
                        git_provider=ProviderType.AZURE_DEVOPS,
                        is_public=False,  # Azure DevOps repos are private by default
                        stargazers_count=None,
                        link_header=None,
                        pushed_at=None,
                    )
                )

            return result
        except Exception as e:
            logger.error(f'Error searching Azure DevOps repositories: {e}')
            return []

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user.

        Returns:
            A list of suggested tasks including:
            - Open issues assigned to the user
            - Pull requests authored by the user with:
              - Merge conflicts
              - Failing checks
              - Unresolved comments
        """
        tasks: list[SuggestedTask] = []

        try:
            # Get open work items (bugs/issues)
            await self._get_work_item_tasks(tasks)

            # Get pull request tasks
            await self._get_pull_request_tasks(tasks)

            return tasks
        except Exception as e:
            logger.error(f'Error getting Azure DevOps suggested tasks: {e}')
            return []

    async def _get_work_item_tasks(self, tasks: list[SuggestedTask]) -> None:
        """Get work item tasks using WIQL query."""
        try:
            # Use WIQL to query for open bugs
            wiql_url = f'{self.base_url}/wit/wiql'
            wiql_params = {'api-version': '7.1-preview.2'}

            wiql_query = {
                'query': """
                    select [System.Id],
                        [System.WorkItemType],
                        [System.Title],
                        [System.State],
                        [System.TeamProject]
                    from WorkItems
                    where [System.WorkItemType] = 'Bug'
                    and [System.State] <> 'Closed'
                    and [System.State] <> 'Resolved'
                    order by [System.ChangedDate] desc
                """
            }

            wiql_data, _ = await self._make_request(
                wiql_url,
                params=wiql_params,
                method=RequestMethod.POST,
                json_data=wiql_query,
            )

            if not wiql_data or not isinstance(wiql_data, dict):
                return

            work_items = wiql_data.get('workItems', [])[:10]  # Limit to 10

            # Get full work item details
            for work_item in work_items:
                work_item_id = work_item.get('id')
                if not work_item_id:
                    continue

                # Get work item details
                work_item_url = f'{self.base_url}/wit/workitems/{work_item_id}'
                work_item_params = {'api-version': '7.1-preview.3'}

                work_item_data, _ = await self._make_request(
                    work_item_url, params=work_item_params
                )

                if work_item_data and isinstance(work_item_data, dict):
                    fields = work_item_data.get('fields', {})
                    project_name = fields.get('System.TeamProject', '')

                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.AZURE_DEVOPS,
                            task_type=TaskType.OPEN_ISSUE,
                            repo=project_name,
                            issue_number=work_item_id,
                            title=fields.get('System.Title', ''),
                        )
                    )

        except Exception as e:
            logger.warning(f'Error getting work item tasks: {e}')

    async def _get_pull_request_tasks(self, tasks: list[SuggestedTask]) -> None:
        """Get pull request tasks."""
        try:
            # Get all repositories
            repos_url = f'{self.base_url}/git/repositories'
            repos_params = {'api-version': '7.1-preview.1'}

            repos_data, _ = await self._make_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                return

            repositories = repos_data.get('value', [])

            # For each repository, get pull requests
            for repo in repositories:
                project_name = repo.get('project', {}).get('name', '')
                repo_name = repo.get('name', '')
                repo_id = repo.get('id', '')
                full_repo_name = f'{project_name}/{repo_name}'

                if not project_name or not repo_id:
                    continue

                # Get active pull requests
                prs_url = f'{self.base_url}/git/repositories/{repo_id}/pullrequests'
                prs_params = {
                    'api-version': '7.1-preview.1',
                    'searchCriteria.status': 'active',
                }

                prs_data, _ = await self._make_request(prs_url, params=prs_params)

                if not prs_data or not isinstance(prs_data, dict):
                    continue

                pull_requests = prs_data.get('value', [])

                for pr in pull_requests:
                    pr_id = pr.get('pullRequestId')
                    if not pr_id:
                        continue

                    task_type = None

                    # Check for merge conflicts
                    if pr.get('mergeStatus') == 'conflicts':
                        task_type = TaskType.MERGE_CONFLICTS
                    else:
                        # Check for failing policy evaluations
                        try:
                            policy_url = f'{self.base_url}/policy/evaluations'
                            policy_params = {
                                'api-version': '7.1-preview.1',
                                'artifactId': f'vstfs:///CodeReview/CodeReviewId/{project_name}/{pr_id}',
                            }

                            policy_data, _ = await self._make_request(
                                policy_url, params=policy_params
                            )

                            if policy_data and isinstance(policy_data, dict):
                                evaluations = policy_data.get('value', [])
                                has_failing_checks = any(
                                    eval.get('status') == 'rejected'
                                    for eval in evaluations
                                )

                                if has_failing_checks:
                                    task_type = TaskType.FAILING_CHECKS
                        except Exception:
                            # Policy evaluations might not be accessible, continue
                            pass

                        # Check for unresolved comments if no other issues found
                        if not task_type:
                            try:
                                threads_url = f'{self.base_url}/git/repositories/{repo_id}/pullRequests/{pr_id}/threads'
                                threads_params = {'api-version': '7.1-preview.1'}

                                threads_data, _ = await self._make_request(
                                    threads_url, params=threads_params
                                )

                                if threads_data and isinstance(threads_data, dict):
                                    threads = threads_data.get('value', [])
                                    has_unresolved_comments = any(
                                        thread.get('status') == 'active'
                                        and not thread.get('isDeleted', False)
                                        for thread in threads
                                    )

                                    if has_unresolved_comments:
                                        task_type = TaskType.UNRESOLVED_COMMENTS
                            except Exception:
                                # Threads might not be accessible, continue
                                pass

                    # Add the task if we identified a specific issue
                    if task_type:
                        tasks.append(
                            SuggestedTask(
                                git_provider=ProviderType.AZURE_DEVOPS,
                                task_type=task_type,
                                repo=full_repo_name,
                                issue_number=pr_id,
                                title=pr.get('title', ''),
                            )
                        )

        except Exception as e:
            logger.warning(f'Error getting pull request tasks: {e}')

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Get repository details from repository name.

        Args:
            repository: The repository name (format: project/repo)

        Returns:
            The repository details
        """
        try:
            # Parse the repository name (expected format: project/repo)
            parts = repository.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f'Invalid repository name format: {repository}. Expected format: project/repo'
                )

            project_name, repo_name = parts

            # Get repositories for the specific project
            repos_url = f'{self.base_url}/git/repositories'
            repos_params = {'api-version': '7.1-preview.1', 'project': project_name}

            repos_data, _ = await self._make_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                raise ValueError(f'Repository not found: {repository}')

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == repo_name.lower()
                ),
                None,
            )

            if not repo:
                raise ValueError(f'Repository not found: {repository}')

            return Repository(
                id=repo.get('id', ''),
                full_name=f'{project_name}/{repo_name}',
                git_provider=ProviderType.AZURE_DEVOPS,
                is_public=False,  # Azure DevOps repos are private by default
                stargazers_count=None,
                link_header=None,
                pushed_at=None,
            )
        except Exception as e:
            logger.error(f'Error getting Azure DevOps repository details: {e}')
            raise AuthenticationError(f'Failed to get repository details: {e}')

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository.

        Args:
            repository: The repository name (format: project/repo)

        Returns:
            A list of branches
        """
        try:
            # Parse the repository name (expected format: project/repo)
            parts = repository.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f'Invalid repository name format: {repository}. Expected format: project/repo'
                )

            project_name, repo_name = parts

            # First, get the repository ID
            repo_details = await self.get_repository_details_from_repo_name(repository)
            repo_id = repo_details.id

            # Get the branches (refs) for the repository
            refs_url = f'{self.base_url}/git/repositories/{repo_id}/refs'
            refs_params = {
                'api-version': '7.1-preview.1',
                'filter': 'heads/',  # Only get branch refs, not tags
            }

            refs_data, _ = await self._make_request(refs_url, params=refs_params)

            if not refs_data or not isinstance(refs_data, dict):
                return []

            refs = refs_data.get('value', [])

            # Convert to Branch objects
            result = []
            for ref in refs:
                # Extract branch name from ref name (remove 'refs/heads/' prefix)
                ref_name = ref.get('name', '')
                if ref_name.startswith('refs/heads/'):
                    branch_name = ref_name[len('refs/heads/') :]

                    result.append(
                        Branch(
                            name=branch_name,
                            commit_sha=ref.get('objectId', ''),
                            protected=False,  # Azure DevOps doesn't expose this information directly
                            last_push_date=None,  # Azure DevOps doesn't expose this information directly
                        )
                    )

            return result
        except Exception as e:
            logger.error(f'Error getting Azure DevOps branches: {e}')
            return []
