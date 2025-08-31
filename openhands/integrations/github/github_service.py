import os

from pydantic import SecretStr

from openhands.integrations.github.github_http_client import GitHubHTTPClient
from openhands.integrations.github.service import (
    GitHubBranchesMixin,
    GitHubFeaturesMixin,
    GitHubPRsMixin,
    GitHubReposMixin,
    GitHubResolverMixin,
)
from openhands.integrations.service_types import (
    BaseGitService,
    GitService,
    InstallationsService,
    ProviderType,
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

        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.BASE_URL = self.github_http_client.BASE_URL
        self.GRAPHQL_URL = self.github_http_client.GRAPHQL_URL

    @property
    def provider(self) -> str:
        return ProviderType.GITHUB.value


github_service_cls = os.environ.get(
    'OPENHANDS_GITHUB_SERVICE_CLS',
    'openhands.integrations.github.github_service.GitHubService',
)
GithubServiceImpl = get_impl(GitHubService, github_service_cls)
