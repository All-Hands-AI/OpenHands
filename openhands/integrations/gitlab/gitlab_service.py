import logging
import os
from datetime import datetime
from typing import Any

import httpx
from pydantic import SecretStr

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
    UnknownException,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl

logger = logging.getLogger(__name__)


class GitLabService(BaseGitService, GitService):
    """Default implementation of GitService for GitLab integration.

    TODO: This doesn't seem a good candidate for the get_impl() pattern. What are the abstract methods we should actually separate and implement here?
    This is an extension point in OpenHands that allows applications to customize GitLab
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.gitlab_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

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
        base_domain: str | None = None,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager

        if token:
            self.token = token

        if base_domain:
            self.BASE_URL = f'https://{base_domain}/api/v4'
            self.GRAPHQL_URL = f'https://{base_domain}/api/graphql'

    @property
    def provider(self) -> str:
        return ProviderType.GITLAB.value

    async def _get_gitlab_headers(self) -> dict[str, Any]:
        """
        Retrieve the GitLab Token to construct the headers
        """
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'Bearer {self.token.get_secret_value()}',
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
                gitlab_headers = await self._get_gitlab_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=gitlab_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    gitlab_headers = await self._get_gitlab_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=gitlab_headers,
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

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> Any:
        """
        Execute a GraphQL query against the GitLab GraphQL API

        Args:
            query: The GraphQL query string
            variables: Optional variables for the GraphQL query

        Returns:
            The data portion of the GraphQL response
        """
        if variables is None:
            variables = {}
        try:
            async with httpx.AsyncClient() as client:
                gitlab_headers = await self._get_gitlab_headers()
                # Add content type header for GraphQL
                gitlab_headers['Content-Type'] = 'application/json'

                payload = {
                    'query': query,
                    'variables': variables if variables is not None else {},
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
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        # Use a default avatar URL if not provided
        # In some self-hosted GitLab instances, the avatar_url field may be returned as None.
        avatar_url = response.get('avatar_url') or ''

        return User(
            id=str(response.get('id', '')),
            login=response.get('username'),  # type: ignore[call-arg]
            avatar_url=avatar_url,
            name=response.get('name'),
            email=response.get('email'),
            company=response.get('organization'),
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

        response, _ = await self._make_request(url, params)
        repos = [
            Repository(
                id=str(repo.get('id')),
                full_name=repo.get('path_with_namespace'),
                stargazers_count=repo.get('star_count'),
                git_provider=ProviderType.GITLAB,
                is_public=True,
                owner_type=(
                    OwnerType.ORGANIZATION
                    if repo.get('namespace', {}).get('kind') == 'group'
                    else OwnerType.USER
                ),
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
            response, headers = await self._make_request(url, params)

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
                id=str(repo.get('id')),  # type: ignore[arg-type]
                full_name=repo.get('path_with_namespace'),  # type: ignore[arg-type]
                stargazers_count=repo.get('star_count'),
                git_provider=ProviderType.GITLAB,
                is_public=repo.get('visibility') == 'public',
                owner_type=(
                    OwnerType.ORGANIZATION
                    if repo.get('namespace', {}).get('kind') == 'group'
                    else OwnerType.USER
                ),
            )
            for repo in all_repos
        ]

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories.

        Returns:
        - Merge requests authored by the user.
        - Issues assigned to the user.
        """
        # Get user info to use in queries
        user = await self.get_user()
        username = user.login

        # GraphQL query to get merge requests
        query = """
        query GetUserTasks {
          currentUser {
            authoredMergeRequests(state: opened, sort: UPDATED_DESC, first: 100) {
              nodes {
                id
                iid
                title
                project {
                  fullPath
                }
                conflicts
                mergeStatus
                pipelines(first: 1) {
                  nodes {
                    status
                  }
                }
                discussions(first: 100) {
                  nodes {
                    notes {
                      nodes {
                        resolvable
                        resolved
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        try:
            tasks: list[SuggestedTask] = []

            # Get merge requests using GraphQL
            response = await self.execute_graphql_query(query)
            data = response.get('currentUser', {})

            # Process merge requests
            merge_requests = data.get('authoredMergeRequests', {}).get('nodes', [])
            for mr in merge_requests:
                repo_name = mr.get('project', {}).get('fullPath', '')
                mr_number = mr.get('iid')
                title = mr.get('title', '')

                # Start with default task type
                task_type = TaskType.OPEN_PR

                # Check for specific states
                if mr.get('conflicts'):
                    task_type = TaskType.MERGE_CONFLICTS
                elif (
                    mr.get('pipelines', {}).get('nodes', [])
                    and mr.get('pipelines', {}).get('nodes', [])[0].get('status')
                    == 'FAILED'
                ):
                    task_type = TaskType.FAILING_CHECKS
                else:
                    # Check for unresolved comments
                    has_unresolved_comments = False
                    for discussion in mr.get('discussions', {}).get('nodes', []):
                        for note in discussion.get('notes', {}).get('nodes', []):
                            if note.get('resolvable') and not note.get('resolved'):
                                has_unresolved_comments = True
                                break
                        if has_unresolved_comments:
                            break

                    if has_unresolved_comments:
                        task_type = TaskType.UNRESOLVED_COMMENTS

                # Only add the task if it's not OPEN_PR
                if task_type != TaskType.OPEN_PR:
                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.GITLAB,
                            task_type=task_type,
                            repo=repo_name,
                            issue_number=mr_number,
                            title=title,
                        )
                    )

            # Get assigned issues using REST API
            url = f'{self.BASE_URL}/issues'
            params = {
                'assignee_username': username,
                'state': 'opened',
                'scope': 'assigned_to_me',
            }

            issues_response, _ = await self._make_request(
                method=RequestMethod.GET, url=url, params=params
            )

            # Process issues
            for issue in issues_response:
                repo_name = (
                    issue.get('references', {}).get('full', '').split('#')[0].strip()
                )
                issue_number = issue.get('iid')
                title = issue.get('title', '')

                tasks.append(
                    SuggestedTask(
                        git_provider=ProviderType.GITLAB,
                        task_type=TaskType.OPEN_ISSUE,
                        repo=repo_name,
                        issue_number=issue_number,
                        title=title,
                    )
                )

            return tasks
        except Exception:
            return []

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        encoded_name = repository.replace('/', '%2F')

        url = f'{self.BASE_URL}/projects/{encoded_name}'
        repo, _ = await self._make_request(url)

        return Repository(
            id=str(repo.get('id')),
            full_name=repo.get('path_with_namespace'),
            stargazers_count=repo.get('star_count'),
            git_provider=ProviderType.GITLAB,
            is_public=repo.get('visibility') == 'public',
            owner_type=(
                OwnerType.ORGANIZATION
                if repo.get('namespace', {}).get('kind') == 'group'
                else OwnerType.USER
            ),
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""
        encoded_name = repository.replace('/', '%2F')
        url = f'{self.BASE_URL}/projects/{encoded_name}/repository/branches'

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
                branch = Branch(
                    name=branch_data.get('name'),
                    commit_sha=branch_data.get('commit', {}).get('id', ''),
                    protected=branch_data.get('protected', False),
                    last_push_date=branch_data.get('commit', {}).get('committed_date'),
                )
                all_branches.append(branch)

            page += 1

            # Check if we've reached the last page
            link_header = headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break

        return all_branches

    async def create_mr(
        self,
        id: int | str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> str:
        """
        Creates a merge request in GitLab

        Args:
            id: The ID or URL-encoded path of the project
            source_branch: The name of the branch where your changes are implemented
            target_branch: The name of the branch you want the changes merged into
            title: The title of the merge request (optional, defaults to a generic title)
            description: The description of the merge request (optional)
            labels: A list of labels to apply to the merge request (optional)

        Returns:
            - MR URL when successful
            - Error message when unsuccessful
        """

        # Convert string ID to URL-encoded path if needed
        project_id = str(id).replace('/', '%2F') if isinstance(id, str) else id
        url = f'{self.BASE_URL}/projects/{project_id}/merge_requests'

        # Set default description if none provided
        if not description:
            description = f'Merging changes from {source_branch} into {target_branch}'

        # Prepare the request payload
        payload = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title,
            'description': description,
        }

        # Add labels if provided
        if labels and len(labels) > 0:
            payload['labels'] = ','.join(labels)

        # Make the POST request to create the MR
        response, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        return response['web_url']

    def _determine_microagents_path(self, repository_name: str) -> str:
        """Determine the microagents directory path based on repository name."""
        actual_repo_name = repository_name.split('/')[-1]

        if actual_repo_name == 'openhands-config':
            # For GitLab with repository name "openhands-config", scan "microagents" folder
            return 'microagents'
        else:
            # Default behavior: look for .openhands/microagents directory
            return '.openhands/microagents'

    def _create_microagent_response(self, file_name: str, path: str) -> dict:
        """Create a microagent response from basic file information."""
        # Extract name without extension
        name = file_name.replace('.md', '').replace('.cursorrules', 'cursorrules')

        return {
            'name': name,
            'path': path,
            'created_at': datetime.now().isoformat(),
        }

    async def _process_cursorrules_file(
        self, client: httpx.AsyncClient, base_url: str
    ) -> dict | None:
        """Check if .cursorrules file exists and return basic metadata."""
        try:
            headers = await self._get_gitlab_headers()
            cursorrules_response = await client.get(
                f'{base_url}/repository/files/.cursorrules/raw', headers=headers
            )
            if cursorrules_response.status_code == 200:
                return self._create_microagent_response('.cursorrules', '.cursorrules')
        except Exception as e:
            logger.warning(f'Error checking .cursorrules: {str(e)}')
        return None

    async def _process_gitlab_md_files(
        self, client: httpx.AsyncClient, tree_items: list
    ) -> list[dict]:
        """Process .md files from GitLab tree items without fetching content."""
        microagents = []

        for item in tree_items:
            if (
                item['type'] == 'blob'
                and item['name'].endswith('.md')
                and item['name'] != 'README.md'
            ):
                try:
                    microagents.append(
                        self._create_microagent_response(item['name'], item['path'])
                    )
                except Exception as e:
                    logger.warning(
                        f'Error processing microagent {item["name"]}: {str(e)}'
                    )

        return microagents

    async def get_microagents(self, repository: str) -> list[dict]:
        """Fetch microagents from GitLab repository using GitLab API.

        Args:
            repository: Repository name in format 'owner/repo' or 'domain/owner/repo'

        Returns:
            List of microagents found in the repository (without content for performance)
        """
        microagents_path = self._determine_microagents_path(repository)

        # URL encode the repository name for GitLab API
        project_id = repository.replace('/', '%2F')

        # Determine base URL - check if it's a self-hosted GitLab instance
        if '/' in repository and not repository.startswith('gitlab.com/'):
            # Handle self-hosted GitLab (e.g., 'gitlab.example.com/owner/repo')
            parts = repository.split('/')
            if len(parts) >= 3:
                domain = parts[0]
                project_id = '/'.join(parts[1:]).replace('/', '%2F')
                base_url = f'https://{domain}/api/v4/projects/{project_id}'
            else:
                base_url = f'{self.BASE_URL}/projects/{project_id}'
        else:
            base_url = f'{self.BASE_URL}/projects/{project_id}'

        microagents = []

        async with httpx.AsyncClient() as client:
            try:
                headers = await self._get_gitlab_headers()
                # Use repository's default branch (no ref parameter)
                tree_response = await client.get(
                    f'{base_url}/repository/tree',
                    headers=headers,
                    params={'path': microagents_path, 'recursive': 'true'},
                )

                if tree_response.status_code == 404:
                    logger.info(
                        f'No microagents directory found in {repository} at {microagents_path}'
                    )
                    return []

                tree_response.raise_for_status()
                tree_items = tree_response.json()

                # Process .cursorrules if it exists
                cursorrules_response = await self._process_cursorrules_file(
                    client, base_url
                )
                if cursorrules_response:
                    microagents.append(cursorrules_response)

                # Process .md files
                md_microagents = await self._process_gitlab_md_files(client, tree_items)
                microagents.extend(md_microagents)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.info(
                        f'No microagents directory found in {repository} at {microagents_path}'
                    )
                    return []
                raise RuntimeError(
                    f'Failed to fetch microagents from GitLab: {e.response.status_code} {e.response.text}'
                )
            except Exception as e:
                raise RuntimeError(f'Error fetching microagents from GitLab: {str(e)}')

        return microagents

    async def get_microagent_content(self, repository: str, file_path: str) -> str:
        """Fetch individual file content from GitLab repository.

        Args:
            repository: Repository name in format 'owner/repo' or 'domain/owner/repo'
            file_path: Path to the file within the repository

        Returns:
            File content as string

        Raises:
            RuntimeError: If file cannot be fetched or doesn't exist
        """
        headers = await self._get_gitlab_headers()

        # URL encode the repository name and file path for GitLab API
        project_id = repository.replace('/', '%2F')
        encoded_file_path = file_path.replace('/', '%2F')

        # Determine base URL - check if it's a self-hosted GitLab instance
        if '/' in repository and not repository.startswith('gitlab.com/'):
            # Handle self-hosted GitLab (e.g., 'gitlab.example.com/owner/repo')
            parts = repository.split('/')
            if len(parts) >= 3:
                domain = parts[0]
                project_id = '/'.join(parts[1:]).replace('/', '%2F')
                base_url = f'https://{domain}/api/v4/projects/{project_id}'
            else:
                base_url = f'{self.BASE_URL}/projects/{project_id}'
        else:
            base_url = f'{self.BASE_URL}/projects/{project_id}'

        file_url = f'{base_url}/repository/files/{encoded_file_path}/raw'

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(file_url, headers=headers)

                if response.status_code == 404:
                    raise RuntimeError(
                        f'File not found: {file_path} in repository {repository}'
                    )

                response.raise_for_status()
                return response.text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise RuntimeError(
                        f'File not found: {file_path} in repository {repository}'
                    )
                raise RuntimeError(
                    f'Failed to fetch file from GitLab: {e.response.status_code} {e.response.text}'
                )
            except Exception as e:
                raise RuntimeError(f'Error fetching file from GitLab: {str(e)}')


gitlab_service_cls = os.environ.get(
    'OPENHANDS_GITLAB_SERVICE_CLS',
    'openhands.integrations.gitlab.gitlab_service.GitLabService',
)
GitLabServiceImpl = get_impl(GitLabService, gitlab_service_cls)
