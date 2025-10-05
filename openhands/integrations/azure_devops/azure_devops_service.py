from typing import Any
from urllib.parse import quote

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.protocols.http_client import HTTPClient
from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    GitService,
    MicroagentContentResponse,
    PaginatedBranchesResponse,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    TaskType,
    User,
)
from openhands.server.types import AppMode


class AzureDevOpsServiceImpl(BaseGitService, HTTPClient, GitService):
    """Default implementation of GitService for Azure DevOps integration.

    This is an extension point in OpenHands that allows applications to customize Azure DevOps
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.azure_devops_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

    token: SecretStr = SecretStr('')
    refresh = False
    organization: str = ''

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
            # Parse organization from base_domain
            # Strip URL prefix if present (e.g., "https://dev.azure.com/org" -> "org")
            domain_path = base_domain
            if '://' in domain_path:
                # Remove protocol and domain, keep only path
                domain_path = domain_path.split('://', 1)[1]
                if '/' in domain_path:
                    domain_path = domain_path.split('/', 1)[1]

            # Format expected: organization (e.g., "contoso")
            # Take first part only (in case user still enters org/project)
            parts = domain_path.split('/')
            if len(parts) >= 1:
                self.organization = parts[0]

    @property
    def provider(self) -> str:
        return ProviderType.AZURE_DEVOPS.value

    @property
    def base_url(self) -> str:
        """Get the base URL for Azure DevOps API calls."""
        return f'https://dev.azure.com/{self.organization}'

    @staticmethod
    def _url_encode(value: str) -> str:
        """URL-encode a value to handle spaces and special characters in Azure DevOps names.

        Args:
            value: The string to encode (e.g., repository name, project name)

        Returns:
            URL-encoded string
        """
        return quote(value, safe='')

    async def _get_azure_devops_headers(self) -> dict[str, Any]:
        """Retrieve the Azure DevOps Token to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        # Azure DevOps uses Basic authentication with PAT
        # The username is ignored (empty string), and the password is the PAT
        import base64

        auth_str = base64.b64encode(
            f':{self.token.get_secret_value()}'.encode()
        ).decode()

        return {
            'Authorization': f'Basic {auth_str}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    async def _get_headers(self) -> dict[str, Any]:
        """Retrieve the Azure DevOps headers."""
        return await self._get_azure_devops_headers()

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
                azure_devops_headers = await self._get_azure_devops_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=azure_devops_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    azure_devops_headers = await self._get_azure_devops_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=azure_devops_headers,
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
        """Get the authenticated user's information."""
        url = f'{self.base_url}/_apis/connectionData?api-version=7.1-preview.1'
        response, _ = await self._make_request(url)

        # Extract authenticated user details
        authenticated_user = response.get('authenticatedUser', {})
        user_id = authenticated_user.get('id', '')
        display_name = authenticated_user.get('providerDisplayName', '')

        # Get descriptor for potential additional details
        authenticated_user.get('descriptor', '')

        return User(
            id=str(user_id),
            login=display_name,
            avatar_url='',
            name=display_name,
            email='',
            company=None,
        )

    async def search_repositories(
        self,
        query: str,
        per_page: int = 30,
        sort: str = 'updated',
        order: str = 'desc',
        public: bool = False,
        app_mode: AppMode = AppMode.OSS,
    ) -> list[Repository]:
        """Search for repositories in Azure DevOps."""
        # Get all repositories across all projects in the organization
        url = f'{self.base_url}/_apis/git/repositories?api-version=7.1'

        response, _ = await self._make_request(url)

        # Filter repositories by query if provided
        repos = response.get('value', [])
        if query:
            repos = [
                repo for repo in repos if query.lower() in repo.get('name', '').lower()
            ]

        # Limit to per_page
        repos = repos[:per_page]

        return [
            Repository(
                id=str(repo.get('id')),
                full_name=f'{self.organization}/{repo.get("project", {}).get("name", "")}/{repo.get("name")}',
                git_provider=ProviderType.AZURE_DEVOPS,
                is_public=False,  # Azure DevOps repos are private by default
            )
            for repo in repos
        ]

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user."""
        MAX_REPOS = 1000

        # Get all projects first
        projects_url = f'{self.base_url}/_apis/projects?api-version=7.1'
        projects_response, _ = await self._make_request(projects_url)
        projects = projects_response.get('value', [])

        all_repos = []

        # For each project, get its repositories
        for project in projects:
            project_name = project.get('name')
            # URL-encode project name to handle spaces and special characters
            encoded_project_name = self._url_encode(project_name)
            repos_url = f'{self.base_url}/{encoded_project_name}/_apis/git/repositories?api-version=7.1'
            repos_response, _ = await self._make_request(repos_url)
            repos = repos_response.get('value', [])

            for repo in repos:
                all_repos.append(
                    {
                        'id': repo.get('id'),
                        'name': repo.get('name'),
                        'project_name': project_name,
                        'updated_date': repo.get('lastUpdateTime'),
                    }
                )

                if len(all_repos) >= MAX_REPOS:
                    break

            if len(all_repos) >= MAX_REPOS:
                break

        # Sort repositories based on the sort parameter
        if sort == 'updated':
            all_repos.sort(key=lambda r: r.get('updated_date', ''), reverse=True)
        elif sort == 'name':
            all_repos.sort(key=lambda r: r.get('name', '').lower())

        return [
            Repository(
                id=str(repo.get('id')),
                full_name=f'{self.organization}/{repo.get("project_name")}/{repo.get("name")}',
                git_provider=ProviderType.AZURE_DEVOPS,
                is_public=False,  # Azure DevOps repos are private by default
            )
            for repo in all_repos[:MAX_REPOS]
        ]

    async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        """Get repositories for the authenticated user (alias for get_repositories)."""
        return await self.get_repositories(sort, app_mode)

    def _parse_repository_response(
        self, repo: dict, project_name: str, link_header: str | None = None
    ) -> Repository:
        """Parse an Azure DevOps API repository response into a Repository object.

        Args:
            repo: Repository data from Azure DevOps API
            project_name: The project name the repository belongs to
            link_header: Optional link header for pagination

        Returns:
            Repository object
        """
        return Repository(
            id=str(repo.get('id')),
            full_name=f'{self.organization}/{project_name}/{repo.get("name")}',
            git_provider=ProviderType.AZURE_DEVOPS,
            is_public=False,  # Azure DevOps repos are private by default
            link_header=link_header,
        )

    async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get a page of repositories for the authenticated user."""
        # Get all repos first, then paginate manually
        # Azure DevOps doesn't have native pagination for repositories
        all_repos = await self.get_repositories(sort, AppMode.SAAS)

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Filter by query if provided
        if query:
            query_lower = query.lower()
            all_repos = [
                repo for repo in all_repos if query_lower in repo.full_name.lower()
            ]

        return all_repos[start_idx:end_idx]

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories."""
        # Azure DevOps requires querying each project separately for PRs and work items
        # Since we no longer specify a single project, we need to query all projects
        # Get all projects first
        projects_url = f'{self.base_url}/_apis/projects?api-version=7.1'
        projects_response, _ = await self._make_request(projects_url)
        projects = projects_response.get('value', [])

        # Get user info
        user = await self.get_user()
        tasks = []

        # Query each project for pull requests and work items
        for project in projects:
            project_name = project.get('name')
            # URL-encode project name to handle spaces and special characters
            encoded_project_name = self._url_encode(project_name)

            try:
                # Get pull requests created by the user in this project
                url = f'{self.base_url}/{encoded_project_name}/_apis/git/pullrequests?api-version=7.1&searchCriteria.creatorId={user.id}&searchCriteria.status=active'
                response, _ = await self._make_request(url)

                pull_requests = response.get('value', [])

                for pr in pull_requests:
                    repo_name = pr.get('repository', {}).get('name', '')
                    pr_id = pr.get('pullRequestId')
                    title = pr.get('title', '')

                    # Check for merge conflicts
                    if pr.get('mergeStatus') == 'conflicts':
                        tasks.append(
                            SuggestedTask(
                                git_provider=ProviderType.AZURE_DEVOPS,
                                task_type=TaskType.MERGE_CONFLICTS,
                                repo=f'{self.organization}/{project_name}/{repo_name}',
                                issue_number=pr_id,
                                title=title,
                            )
                        )
                    # Check for failing checks
                    elif pr.get('status') == 'failed':
                        tasks.append(
                            SuggestedTask(
                                git_provider=ProviderType.AZURE_DEVOPS,
                                task_type=TaskType.FAILING_CHECKS,
                                repo=f'{self.organization}/{project_name}/{repo_name}',
                                issue_number=pr_id,
                                title=title,
                            )
                        )
                    # Check for unresolved comments
                    elif pr.get('hasUnresolvedComments', False):
                        tasks.append(
                            SuggestedTask(
                                git_provider=ProviderType.AZURE_DEVOPS,
                                task_type=TaskType.UNRESOLVED_COMMENTS,
                                repo=f'{self.organization}/{project_name}/{repo_name}',
                                issue_number=pr_id,
                                title=title,
                            )
                        )

                # Get work items assigned to the user in this project
                work_items_url = f'{self.base_url}/{encoded_project_name}/_apis/wit/wiql?api-version=7.1'
                wiql_query = {
                    'query': "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @me AND [System.State] = 'Active'"
                }

                work_items_response, _ = await self._make_request(
                    url=work_items_url, params=wiql_query, method=RequestMethod.POST
                )

                work_item_references = work_items_response.get('workItems', [])

                # Get details for each work item
                for work_item_ref in work_item_references:
                    work_item_id = work_item_ref.get('id')
                    work_item_url = f'{self.base_url}/{encoded_project_name}/_apis/wit/workitems/{work_item_id}?api-version=7.1'
                    work_item, _ = await self._make_request(work_item_url)

                    title = work_item.get('fields', {}).get('System.Title', '')

                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.AZURE_DEVOPS,
                            task_type=TaskType.OPEN_ISSUE,
                            repo=f'{self.organization}/{project_name}',
                            issue_number=work_item_id,
                            title=title,
                        )
                    )
            except Exception:
                # Skip projects that fail (e.g., no access, no work items enabled)
                continue

        return tasks

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets repository details from repository name."""
        # Parse repository string: organization/project/repo
        parts = repository.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )

        org = parts[0]
        project = parts[1]
        repo_name = parts[2]

        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo_name = self._url_encode(repo_name)

        url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}?api-version=7.1'
        repo, _ = await self._make_request(url)

        return Repository(
            id=str(repo.get('id')),
            full_name=f'{org}/{project}/{repo.get("name")}',
            git_provider=ProviderType.AZURE_DEVOPS,
            is_public=False,  # Azure DevOps repos are private by default
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository."""
        # Parse repository string: organization/project/repo
        parts = repository.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )

        org = parts[0]
        project = parts[1]
        repo_name = parts[2]

        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo_name = self._url_encode(repo_name)

        url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/refs?api-version=7.1&filter=heads/'

        # Set maximum branches to fetch
        MAX_BRANCHES = 1000

        response, _ = await self._make_request(url)
        branches_data = response.get('value', [])

        all_branches = []

        for branch_data in branches_data:
            # Extract branch name from the ref (e.g., "refs/heads/main" -> "main")
            name = branch_data.get('name', '').replace('refs/heads/', '')

            # Get the commit details for this branch
            object_id = branch_data.get('objectId', '')
            commit_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/commits/{object_id}?api-version=7.1'
            commit_data, _ = await self._make_request(commit_url)

            # Check if the branch is protected
            policy_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/policy/configurations?api-version=7.1&repositoryId={encoded_repo_name}&refName=refs/heads/{name}'
            policy_data, _ = await self._make_request(policy_url)
            is_protected = len(policy_data.get('value', [])) > 0

            branch = Branch(
                name=name,
                commit_sha=object_id,
                protected=is_protected,
                last_push_date=commit_data.get('committer', {}).get('date'),
            )
            all_branches.append(branch)

            if len(all_branches) >= MAX_BRANCHES:
                break

        return all_branches

    async def get_paginated_branches(
        self, repository: str, page: int = 1, per_page: int = 30
    ) -> PaginatedBranchesResponse:
        """Get branches for a repository with pagination."""
        # Parse repository string: organization/project/repo
        parts = repository.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )

        org = parts[0]
        project = parts[1]
        repo_name = parts[2]

        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo_name = self._url_encode(repo_name)

        # First, get the repository to get its ID
        repo_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}?api-version=7.1'
        repo_data, _ = await self._make_request(repo_url)
        repo_id = repo_data.get(
            'id', repo_name
        )  # Fall back to repo_name if ID not found

        url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/refs?api-version=7.1&filter=heads/'

        response, _ = await self._make_request(url)
        branches_data = response.get('value', [])

        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = branches_data[start_idx:end_idx]

        branches: list[Branch] = []
        for branch_data in paginated_data:
            # Extract branch name from the ref (e.g., "refs/heads/main" -> "main")
            name = branch_data.get('name', '').replace('refs/heads/', '')

            # Get the commit details for this branch
            object_id = branch_data.get('objectId', '')
            commit_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/commits/{object_id}?api-version=7.1'
            commit_data, _ = await self._make_request(commit_url)

            # Check if the branch is protected using repository ID
            policy_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/policy/configurations?api-version=7.1&repositoryId={repo_id}&refName=refs/heads/{name}'
            policy_data, _ = await self._make_request(policy_url)
            is_protected = len(policy_data.get('value', [])) > 0

            branch = Branch(
                name=name,
                commit_sha=object_id,
                protected=is_protected,
                last_push_date=commit_data.get('committer', {}).get('date'),
            )
            branches.append(branch)

        # Determine if there's a next page
        has_next_page = end_idx < len(branches_data)

        return PaginatedBranchesResponse(
            branches=branches,
            has_next_page=has_next_page,
            current_page=page,
            per_page=per_page,
        )

    async def search_branches(
        self, repository: str, query: str, per_page: int = 30
    ) -> list[Branch]:
        """Search for branches within a repository."""
        # Parse repository string: organization/project/repo
        parts = repository.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )

        org = parts[0]
        project = parts[1]
        repo_name = parts[2]

        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo_name = self._url_encode(repo_name)

        url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/refs?api-version=7.1&filter=heads/'

        try:
            response, _ = await self._make_request(url)
            branches_data = response.get('value', [])

            # Filter branches by query
            filtered_branches = []
            for branch_data in branches_data:
                # Extract branch name from the ref (e.g., "refs/heads/main" -> "main")
                name = branch_data.get('name', '').replace('refs/heads/', '')

                # Check if query matches branch name
                if query.lower() in name.lower():
                    object_id = branch_data.get('objectId', '')

                    # Get commit details for this branch
                    commit_url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo_name}/commits/{object_id}?api-version=7.1'
                    try:
                        commit_data, _ = await self._make_request(commit_url)
                        last_push_date = commit_data.get('committer', {}).get('date')
                    except Exception:
                        last_push_date = None

                    branch = Branch(
                        name=name,
                        commit_sha=object_id,
                        protected=False,  # Skip protected check for search to improve performance
                        last_push_date=last_push_date,
                    )
                    filtered_branches.append(branch)

                    if len(filtered_branches) >= per_page:
                        break

            return filtered_branches
        except Exception:
            # Return empty list on error instead of None
            return []

    async def create_pr(
        self,
        repo_name: str,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str | None = None,
        draft: bool = False,
    ) -> str:
        """Creates a pull request in Azure DevOps.

        Args:
            repo_name: The repository name in format "organization/project/repo"
            source_branch: The source branch name
            target_branch: The target branch name
            title: The title of the pull request
            body: The description of the pull request
            draft: Whether to create a draft pull request

        Returns:
            The URL of the created pull request
        """
        # Parse repository string: organization/project/repo
        parts = repo_name.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repo_name}. Expected format: organization/project/repo'
            )

        org = parts[0]
        project = parts[1]
        repo = parts[2]

        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo = self._url_encode(repo)

        url = f'https://dev.azure.com/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo}/pullrequests?api-version=7.1'

        # Set default body if none provided
        if not body:
            body = f'Merging changes from {source_branch} into {target_branch}'

        payload = {
            'sourceRefName': f'refs/heads/{source_branch}',
            'targetRefName': f'refs/heads/{target_branch}',
            'title': title,
            'description': body,
            'isDraft': draft,
        }

        response, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        # Return the web URL of the created PR
        pr_id = response.get('pullRequestId')
        return f'https://dev.azure.com/{encoded_org}/{encoded_project}/_git/{encoded_repo}/pullrequest/{pr_id}'

    def _parse_repository(self, repository: str) -> tuple[str, str, str]:
        """Parse repository string into organization, project, and repo name.

        Args:
            repository: Repository string in format organization/project/repo

        Returns:
            Tuple of (organization, project, repo_name)
        """
        parts = repository.split('/')
        if len(parts) < 3:
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )
        return parts[0], parts[1], parts[2]

    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file in Azure DevOps."""
        org, project, repo = self._parse_repository(repository)
        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo = self._url_encode(repo)
        return f'{self.base_url}/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo}/items?path=/.cursorrules&api-version=7.1'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory in Azure DevOps.

        Note: For org-level microagents (e.g., 'org/.openhands'), Azure DevOps doesn't support
        this concept, so we raise ValueError to let the caller fall back to other providers.
        """
        parts = repository.split('/')
        if len(parts) < 3:
            # Azure DevOps doesn't support org-level configs, only full repo paths
            raise ValueError(
                f'Invalid repository format: {repository}. Expected format: organization/project/repo'
            )
        org, project, repo = parts[0], parts[1], parts[2]
        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo = self._url_encode(repo)
        return f'{self.base_url}/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo}/items?path=/{microagents_path}&recursionLevel=OneLevel&api-version=7.1'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request. Return None if no parameters needed."""
        return None

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file in Azure DevOps."""
        return (
            not item.get('isFolder', False)
            and item.get('path', '').endswith('.md')
            and not item.get('path', '').endswith('README.md')
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item in Azure DevOps."""
        path = item.get('path', '')
        return path.split('/')[-1] if path else ''

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item in Azure DevOps."""
        return item.get('path', '').lstrip('/')

    async def get_microagent_content(
        self, repository: str, file_path: str
    ) -> MicroagentContentResponse:
        """Get content of a specific microagent file.

        Args:
            repository: Repository name in Azure DevOps format 'org/project/repo'
            file_path: Path to the microagent file

        Returns:
            MicroagentContentResponse with parsed content and triggers
        """
        org, project, repo = self._parse_repository(repository)
        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo = self._url_encode(repo)
        url = f'{self.base_url}/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo}/items?path={file_path}&api-version=7.1'

        try:
            response, _ = await self._make_request(url)
            content = (
                response if isinstance(response, str) else response.get('content', '')
            )

            # Parse the content using the base class method
            return self._parse_microagent_content(content, file_path)
        except Exception as e:
            logger.warning(f'Failed to fetch microagent content from {file_path}: {e}')
            raise

    async def get_pr_details(self, repository: str, pr_number: int) -> dict:
        """Get detailed information about a specific pull request.

        Args:
            repository: Repository name in Azure DevOps format 'org/project/repo'
            pr_number: The pull request number

        Returns:
            Raw API response from Azure DevOps
        """
        org, project, repo = self._parse_repository(repository)
        # URL-encode components to handle spaces and special characters
        encoded_org = self._url_encode(org)
        encoded_project = self._url_encode(project)
        encoded_repo = self._url_encode(repo)
        url = f'{self.base_url}/{encoded_org}/{encoded_project}/_apis/git/repositories/{encoded_repo}/pullrequests/{pr_number}?api-version=7.1'

        response, _ = await self._make_request(url)
        return response

    async def is_pr_open(self, repository: str, pr_number: int) -> bool:
        """Check if a PR is still active (not closed/merged).

        Args:
            repository: Repository name in Azure DevOps format 'org/project/repo'
            pr_number: The PR number to check

        Returns:
            True if PR is active (open), False if closed/merged/abandoned
        """
        try:
            pr_details = await self.get_pr_details(repository, pr_number)
            status = pr_details.get('status', '').lower()
            # Azure DevOps PR statuses: active, abandoned, completed
            return status == 'active'
        except Exception as e:
            logger.warning(
                f'Failed to check PR status for {repository}#{pr_number}: {e}'
            )
            return False
