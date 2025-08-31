import json
from typing import Any, cast

import httpx
from pydantic import SecretStr

from openhands.integrations.protocols.http_client import (
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    UnknownException,
)
from openhands.integrations.service_types import (
    RequestMethod,
    User,
)


class GitHubHTTPClient:
    """
    HTTP client implementation for GitHub API operations.
    Implements HTTPClientInterface and provides common functionality for GitHub API interactions.
    """

    BASE_URL: str
    GRAPHQL_URL: str
    token: SecretStr
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
        self.token = token or SecretStr('')
        self.refresh = False
        self.external_auth_id = external_auth_id
        self.base_domain = base_domain

        # Handle custom domain configuration
        if base_domain and base_domain != 'github.com':
            self.BASE_URL = f'https://{base_domain}/api/v3'
            self.GRAPHQL_URL = f'https://{base_domain}/api/graphql'

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
        """Backward compatibility method."""
        return await self._get_headers()

    async def get_latest_token(self) -> SecretStr | None:  # type: ignore[override]
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
                response = await self._execute_request(
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
                    response = await self._execute_request(
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
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                headers = await self._get_headers()

                response = await client.post(
                    self.GRAPHQL_URL,
                    headers=headers,
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
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

    async def verify_access(self) -> bool:
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True

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

    # Helper methods needed by the HTTP client
    async def _execute_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        """Execute HTTP request."""
        if method == RequestMethod.POST:
            return await client.post(url, headers=headers, json=params)
        return await client.get(url, headers=headers, params=params)

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if the token has expired based on status code."""
        return status_code == 401

    def _handle_http_status_error(self, e: httpx.HTTPStatusError):
        """Handle HTTP status errors."""
        if e.response.status_code == 401:
            return AuthenticationError('Invalid GitHub token')
        elif e.response.status_code == 404:
            return ResourceNotFoundError(f'Resource not found on GitHub API: {e}')
        elif e.response.status_code == 429:
            return RateLimitError('GitHub API rate limit exceeded')

        return UnknownException(f'Unknown error: {e}')

    def _handle_http_error(self, e: httpx.HTTPError):
        """Handle HTTP errors."""
        return UnknownException(f'HTTP error {type(e).__name__} : {e}')


# Backward compatibility alias
GitHubMixinBase = GitHubHTTPClient
