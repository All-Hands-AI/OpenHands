from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Protocol

from httpx import AsyncClient, HTTPError, HTTPStatusError
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.server.types import AppMode


class ProviderType(Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'


class TaskType(str, Enum):
    MERGE_CONFLICTS = 'MERGE_CONFLICTS'
    FAILING_CHECKS = 'FAILING_CHECKS'
    UNRESOLVED_COMMENTS = 'UNRESOLVED_COMMENTS'
    OPEN_ISSUE = 'OPEN_ISSUE'
    OPEN_PR = 'OPEN_PR'


class SuggestedTask(BaseModel):
    git_provider: ProviderType
    task_type: TaskType
    repo: str
    issue_number: int
    title: str

    def get_provider_terms(self) -> dict:
        if self.git_provider == ProviderType.GITLAB:
            return {
                'requestType': 'Merge Request',
                'requestTypeShort': 'MR',
                'apiName': 'GitLab API',
                'tokenEnvVar': 'GITLAB_TOKEN',
                'ciSystem': 'CI pipelines',
                'ciProvider': 'GitLab',
                'requestVerb': 'merge request',
            }
        elif self.git_provider == ProviderType.GITHUB:
            return {
                'requestType': 'Pull Request',
                'requestTypeShort': 'PR',
                'apiName': 'GitHub API',
                'tokenEnvVar': 'GITHUB_TOKEN',
                'ciSystem': 'GitHub Actions',
                'ciProvider': 'GitHub',
                'requestVerb': 'pull request',
            }

        raise ValueError(f'Provider {self.git_provider} for suggested task prompts')

    def get_prompt_for_task(
        self,
    ) -> str:
        task_type = self.task_type
        issue_number = self.issue_number
        repo = self.repo

        env = Environment(
            loader=FileSystemLoader('openhands/integrations/templates/suggested_task')
        )

        template = None
        if task_type == TaskType.MERGE_CONFLICTS:
            template = env.get_template('merge_conflict_prompt.j2')
        elif task_type == TaskType.FAILING_CHECKS:
            template = env.get_template('failing_checks_prompt.j2')
        elif task_type == TaskType.UNRESOLVED_COMMENTS:
            template = env.get_template('unresolved_comments_prompt.j2')
        elif task_type == TaskType.OPEN_ISSUE:
            template = env.get_template('open_issue_prompt.j2')
        else:
            raise ValueError(f'Unsupported task type: {task_type}')

        terms = self.get_provider_terms()

        return template.render(issue_number=issue_number, repo=repo, **terms)


class User(BaseModel):
    id: int
    login: str
    avatar_url: str
    company: str | None = None
    name: str | None = None
    email: str | None = None


class Branch(BaseModel):
    name: str
    commit_sha: str
    protected: bool
    last_push_date: str | None = None  # ISO 8601 format date string


class Repository(BaseModel):
    id: int
    full_name: str
    git_provider: ProviderType
    is_public: bool
    stargazers_count: int | None = None
    link_header: str | None = None
    pushed_at: str | None = None  # ISO 8601 format date string


class AuthenticationError(ValueError):
    """Raised when there is an issue with GitHub authentication."""

    pass


class UnknownException(ValueError):
    """Raised when there is an issue with GitHub communcation."""

    pass


class RateLimitError(ValueError):
    """Raised when the git provider's API rate limits are exceeded."""

    pass


class RequestMethod(Enum):
    POST = 'post'
    GET = 'get'


class BaseGitService(ABC):
    @property
    def provider(self) -> str:
        raise NotImplementedError('Subclasses must implement the provider property')

    # Method used to satisfy mypy for abstract class definition
    @abstractmethod
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]: ...

    async def execute_request(
        self,
        client: AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        if method == RequestMethod.POST:
            return await client.post(url, headers=headers, json=params)
        return await client.get(url, headers=headers, params=params)

    def handle_http_status_error(
        self, e: HTTPStatusError
    ) -> AuthenticationError | RateLimitError | UnknownException:
        if e.response.status_code == 401:
            return AuthenticationError(f'Invalid {self.provider} token')
        elif e.response.status_code == 429:
            logger.warning(f'Rate limit exceeded on {self.provider} API: {e}')
            return RateLimitError('GitHub API rate limit exceeded')

        logger.warning(f'Status error on {self.provider} API: {e}')
        return UnknownException('Unknown error')

    def handle_http_error(self, e: HTTPError) -> UnknownException:
        logger.warning(f'HTTP error on {self.provider} API: {type(e).__name__} : {e}')
        return UnknownException(f'HTTP error {type(e).__name__}')


class GitService(Protocol):
    """Protocol defining the interface for Git service providers"""

    def __init__(
        self,
        user_id: str | None = None,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        external_token_manager: bool = False,
    ) -> None:
        """Initialize the service with authentication details"""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user"""
        ...

    async def get_user(self) -> User:
        """Get the authenticated user's information"""
        ...

    async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
    ) -> list[Repository]:
        """Search for repositories"""
        ...

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user"""
        ...

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks for the authenticated user across all repositories"""
        ...

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets all repository details from repository name"""

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository"""
