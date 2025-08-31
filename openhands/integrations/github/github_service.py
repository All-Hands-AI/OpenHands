import os
from typing import Any

from pydantic import SecretStr

from openhands.integrations.github.service import (
    GitHubBranchesMixin,
    GitHubFeaturesMixin,
    GitHubPRsMixin,
    GitHubReposMixin,
    GitHubResolverMixin,
)
from openhands.integrations.github.service.base import GitHubHTTPClient
from openhands.integrations.service_types import (
    BaseGitService,
    GitService,
    InstallationsService,
    ProviderType,
    RequestMethod,
    User,
)
from openhands.utils.import_utils import get_impl


class GitHubService(
    GitHubBranchesMixin,
    GitHubFeaturesMixin,
    GitHubPRsMixin,
    GitHubReposMixin,
    GitHubResolverMixin,
    BaseGitService,
    GitService,
    InstallationsService,
):
    """
    Assembled GitHub service class combining mixins by feature area.

    Now uses composition for HTTP client functionality via a class variable.
    This allows for incremental migration from mixins to composition.

    This is an extension point in OpenHands that allows applications to customize GitHub
    integration behavior. Applications can substitute their own implementation by:
    1. Creating a class that inherits from GitService
    2. Implementing all required methods
    3. Setting server_config.github_service_class to the fully qualified name of the class

    The class is instantiated via get_impl() in openhands.server.shared.py.
    """

    # Class variable for HTTP client (composition)
    github_http_client: GitHubHTTPClient
    external_auth_id: str | None

    BASE_URL = 'https://api.github.com'
    GRAPHQL_URL = 'https://api.github.com/graphql'
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
    ) -> None:
        self.user_id = user_id
        self.external_auth_id = external_auth_id
        self.external_token_manager = external_token_manager
        self.external_auth_token = external_auth_token

        # Initialize HTTP client with all configuration
        self.github_http_client = GitHubHTTPClient(
            token=token,
            external_auth_id=external_auth_id,
            base_domain=base_domain,
        )

        # Set service-level attributes for backward compatibility
        if token:
            self.token = token

        # Set service-level URLs for backward compatibility
        self.BASE_URL = self.github_http_client.BASE_URL
        self.GRAPHQL_URL = self.github_http_client.GRAPHQL_URL

    @property
    def provider(self) -> str:
        return ProviderType.GITHUB.value

    # Implementation of abstract methods from BaseGitService
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Delegate to HTTP client."""
        return await self.github_http_client._make_request(url, params, method)

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

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a GraphQL query."""
        return await self.github_http_client.execute_graphql_query(query, variables)

    async def _get_github_headers(self) -> dict[str, str]:
        """Get GitHub API headers."""
        return await self.github_http_client._get_github_headers()

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if token has expired based on status code."""
        return self.github_http_client._has_token_expired(status_code)

    async def get_latest_token(self) -> SecretStr | None:
        """Get the latest token."""
        return await self.github_http_client.get_latest_token()

    async def verify_access(self) -> bool:
        """Verify access to GitHub API."""
        return await self.github_http_client.verify_access()

    async def get_user(self) -> User:
        """Get the authenticated user."""
        return await self.github_http_client.get_user()


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
