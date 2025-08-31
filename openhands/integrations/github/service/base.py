from typing import cast

from pydantic import SecretStr

from openhands.integrations.github.github_http_client import GitHubHTTPClient
from openhands.integrations.service_types import (
    BaseGitService,
    RequestMethod,
    User,
)


class GitHubMixinBase(BaseGitService):
    github_http_client: GitHubHTTPClient

    def __init__(
        self,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        base_domain: str | None = None,
    ) -> None:
        """Initialize the GitHub HTTP client with configuration."""
        self.BASE_URL = 'https://api.github.com'
        self.GRAPHQL_URL = 'https://api.github.com/graphql'
        self.token = token or SecretStr('')
        self.refresh = False
        self.external_auth_id = external_auth_id
        self.base_domain = base_domain

        # Handle custom domain configuration
        if base_domain and base_domain != 'github.com':
            self.BASE_URL = f'https://{base_domain}/api/v3'
            self.GRAPHQL_URL = f'https://{base_domain}/api/graphql'

    async def get_latest_token(self) -> SecretStr | None:
        return await self.github_http_client.get_latest_token()

    async def _make_request(self, url, params=None, method=RequestMethod.GET):
        return await self.github_http_client._make_request(url, params, method)

    async def get_user(self):
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        return User(
            id=str(response.get('id', '')),
            login=cast(str, response.get('login') or ''),
            avatar_url=cast(str, response.get('avatar_url') or ''),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )

    async def verify_access(self) -> bool:
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True
