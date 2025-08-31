import json
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.protocols.http_client import (
    HTTPClientProtocol,
    UnknownException,
)
from openhands.integrations.service_types import (
    ProviderType,
    RequestMethod,
)


class GitHubHTTPClient(HTTPClientProtocol):
    """
    HTTP client implementation for GitHub API operations.
    Implements HTTPClientInterface and provides common functionality for GitHub API interactions.
    """

    BASE_URL: str
    GRAPHQL_URL: str
    token: SecretStr | None
    refresh: bool
    external_auth_id: str | None
    base_domain: str | None

    def __init__(
        self,
        token: SecretStr | None = None,
        external_auth_id: str | None = None,
        base_domain: str | None = None,
    ) -> None:
        """Initialize the GitHub HTTP client with configuration."""
        # Set default values
        self.BASE_URL = 'https://api.github.com'
        self.GRAPHQL_URL = 'https://api.github.com/graphql'
        self.token = token
        self.refresh = False
        self.external_auth_id = external_auth_id
        self.base_domain = base_domain

        # Handle custom domain configuration
        if base_domain and base_domain != 'github.com':
            self.BASE_URL = f'https://{base_domain}/api/v3'
            self.GRAPHQL_URL = f'https://{base_domain}/api/graphql'

    @property
    def provider(self) -> str:
        return ProviderType.GITHUB.value

    async def _get_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
        }

    async def _get_github_headers(self) -> dict:
        return await self._get_headers()

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:  # type: ignore[override]
        try:
            async with httpx.AsyncClient() as client:
                headers = await self._get_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    headers = await self._get_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                response_headers: dict = {}
                if 'Link' in response.headers:
                    response_headers['Link'] = response.headers['Link']

                return response.json(), response_headers

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_github_headers()

                response = await client.post(
                    self.GRAPHQL_URL,
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
