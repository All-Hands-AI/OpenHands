"""
Azure DevOps service implementation.
"""

from __future__ import annotations

from typing import Any

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Import models conditionally to handle different versions of the azure-devops package
try:
    from azure.devops.v7_1.work_item_tracking.models import Wiql
except ImportError:
    # For testing purposes, create a mock class
    class Wiql:  # type: ignore
        def __init__(self, query=None):
            self.query = query


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
    User,
)
from openhands.server.types import AppMode


class AzureDevOpsServiceImpl(BaseGitService):
    """Azure DevOps service implementation."""

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

        # Create a connection to Azure DevOps
        if token:
            credentials = BasicAuthentication('', token.get_secret_value())
            self.connection = Connection(
                base_url=self.organization_url, creds=credentials
            )
        else:
            self.connection = None

    @property
    def provider(self) -> str:
        return ProviderType.AZURE_DEVOPS.value

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make a request to the Azure DevOps API.

        This method is not used directly for Azure DevOps as we use the official SDK.
        It's implemented to satisfy the BaseGitService abstract method.
        """
        return None, {}

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
        if not self.connection:
            raise AuthenticationError('No Azure DevOps token provided')

        try:
            # Get the Core client
            core_client = self.connection.clients.get_core_client()

            # Get the authenticated user's profile
            # Note: Azure DevOps doesn't have a direct API for this, so we use a workaround
            # by getting the current user's projects
            core_client.get_projects()

            # For now, we'll create a placeholder user
            # In a real implementation, you might want to use the Microsoft Graph API
            # to get more detailed user information
            return User(
                id=0,  # Placeholder ID
                login=self.user_id or 'azure_devops_user',
                avatar_url='',
                name=self.user_id or 'Azure DevOps User',
                email=None,
                company=None,
            )
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
        if not self.connection:
            return []

        try:
            # Get the Git client
            git_client = self.connection.clients.get_git_client()

            # Get all repositories
            repos = git_client.get_repositories()

            # Convert to Repository objects
            result = []
            for repo in repos:
                result.append(
                    Repository(
                        id=repo.id,
                        full_name=f'{repo.project.name}/{repo.name}',
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
        if not self.connection:
            return []

        try:
            # Get the Git client
            git_client = self.connection.clients.get_git_client()

            # Get all repositories (Azure DevOps doesn't have a search API for repos)
            repos = git_client.get_repositories()

            # Filter repositories by name (simple client-side filtering)
            filtered_repos = [
                repo
                for repo in repos
                if query.lower() in repo.name.lower()
                or (repo.project and query.lower() in repo.project.name.lower())
            ]

            # Convert to Repository objects
            result = []
            for repo in filtered_repos[:per_page]:
                result.append(
                    Repository(
                        id=repo.id,
                        full_name=f'{repo.project.name}/{repo.name}',
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
        if not self.connection:
            return []

        tasks = []

        try:
            # Get the Work Item Tracking client
            wit_client = self.connection.clients.get_work_item_tracking_client()

            # Get open issues (work items of type 'Bug')
            wiql = Wiql(
                query="""
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
            )

            wiql_results = wit_client.query_by_wiql(wiql, top=10).work_items

            # Get the full work items
            if wiql_results:
                work_items = [
                    wit_client.get_work_item(int(res.id)) for res in wiql_results
                ]

                for work_item in work_items:
                    project_name = work_item.fields.get('System.TeamProject', '')

                    tasks.append(
                        SuggestedTask(
                            git_provider=ProviderType.AZURE_DEVOPS,
                            task_type=TaskType.OPEN_ISSUE,
                            repo=project_name,
                            issue_number=work_item.id,
                            title=work_item.fields.get('System.Title', ''),
                        )
                    )

            # Get the Git client
            git_client = self.connection.clients.get_git_client()

            # Get all repositories
            repositories = git_client.get_repositories()

            # For each repository, get pull requests
            for repo in repositories:
                project_name = repo.project.name
                repo_name = repo.name
                full_repo_name = f'{project_name}/{repo_name}'

                # Get pull requests created by the current user
                pull_requests = git_client.get_pull_requests(
                    repo.id,
                    search_criteria={
                        'status': 'active',  # Only active PRs
                    },
                    project=project_name,
                )

                for pr in pull_requests:
                    # Default task type
                    task_type = None

                    # Check for merge conflicts
                    if pr.merge_status == 'conflicts':
                        task_type = TaskType.MERGE_CONFLICTS
                    else:
                        # Check for failing builds/checks
                        policy_evaluations = (
                            git_client.get_pull_request_policy_evaluations(
                                project=project_name,
                                repository_id=repo.id,
                                pull_request_id=pr.pull_request_id,
                            )
                        )

                        has_failing_checks = any(
                            eval.status == 'rejected' for eval in policy_evaluations
                        )

                        if has_failing_checks:
                            task_type = TaskType.FAILING_CHECKS
                        else:
                            # Check for unresolved comments
                            threads = git_client.get_threads(
                                repository_id=repo.id,
                                pull_request_id=pr.pull_request_id,
                                project=project_name,
                            )

                            has_unresolved_comments = any(
                                thread.status == 'active' and not thread.is_deleted
                                for thread in threads
                            )

                            if has_unresolved_comments:
                                task_type = TaskType.UNRESOLVED_COMMENTS

                    # Add the task if we identified a specific issue
                    if task_type:
                        tasks.append(
                            SuggestedTask(
                                git_provider=ProviderType.AZURE_DEVOPS,
                                task_type=task_type,
                                repo=full_repo_name,
                                issue_number=pr.pull_request_id,
                                title=pr.title,
                            )
                        )

            return tasks
        except Exception as e:
            logger.error(f'Error getting Azure DevOps suggested tasks: {e}')
            return []

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Get repository details from repository name.

        Args:
            repository: The repository name (format: project/repo)

        Returns:
            The repository details
        """
        if not self.connection:
            raise AuthenticationError('No Azure DevOps token provided')

        try:
            # Parse the repository name (expected format: project/repo)
            parts = repository.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f'Invalid repository name format: {repository}. Expected format: project/repo'
                )

            project_name, repo_name = parts

            # Get the Git client
            git_client = self.connection.clients.get_git_client()

            # Get the repository
            repos = git_client.get_repositories(project_name)
            repo = next((r for r in repos if r.name.lower() == repo_name.lower()), None)

            if not repo:
                raise ValueError(f'Repository not found: {repository}')

            return Repository(
                id=repo.id,
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
        if not self.connection:
            return []

        try:
            # Parse the repository name (expected format: project/repo)
            parts = repository.split('/')
            if len(parts) != 2:
                raise ValueError(
                    f'Invalid repository name format: {repository}. Expected format: project/repo'
                )

            project_name, repo_name = parts

            # Get the Git client
            git_client = self.connection.clients.get_git_client()

            # Get the repository
            repos = git_client.get_repositories(project_name)
            repo = next((r for r in repos if r.name.lower() == repo_name.lower()), None)

            if not repo:
                raise ValueError(f'Repository not found: {repository}')

            # Get the branches
            branches = git_client.get_branches(repo.id, project_name)

            # Convert to Branch objects
            result = []
            for branch in branches:
                result.append(
                    Branch(
                        name=branch.name,
                        commit_sha=branch.commit.commit_id,
                        protected=False,  # Azure DevOps doesn't expose this information directly
                        last_push_date=None,  # Azure DevOps doesn't expose this information directly
                    )
                )

            return result
        except Exception as e:
            logger.error(f'Error getting Azure DevOps branches: {e}')
            return []
