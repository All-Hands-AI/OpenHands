import json
from typing import Any, Protocol, cast

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    RequestMethod,
    UnknownException,
    User,
)


class HTTPClientInterface(Protocol):
    """Protocol defining the HTTP client interface for GitHub operations."""

    BASE_URL: str
    GRAPHQL_URL: str
    token: SecretStr
    refresh: bool
    external_auth_id: str | None
    base_domain: str | None

    async def _get_github_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user."""
        ...

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make an HTTP request to the GitHub API."""
        ...

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API."""
        ...

    async def verify_access(self) -> bool:
        """Verify that the client has access to the GitHub API."""
        ...

    async def get_user(self) -> User:
        """Get the authenticated user's information."""
        ...


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

    async def _get_github_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
        }

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
                github_headers = await self._get_github_headers()

                # Make initial request
                response = await self._execute_request(
                    client=client,
                    url=url,
                    headers=github_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    github_headers = await self._get_github_headers()
                    response = await self._execute_request(
                        client=client,
                        url=url,
                        headers=github_headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers: dict = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

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
            from openhands.integrations.service_types import AuthenticationError

            return AuthenticationError('Invalid GitHub token')
        elif e.response.status_code == 404:
            from openhands.integrations.service_types import ResourceNotFoundError

            return ResourceNotFoundError(f'Resource not found on GitHub API: {e}')
        elif e.response.status_code == 429:
            from openhands.integrations.service_types import RateLimitError

            return RateLimitError('GitHub API rate limit exceeded')

        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'Unknown error: {e}')

    def _handle_http_error(self, e: httpx.HTTPError):
        """Handle HTTP errors."""
        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'HTTP error {type(e).__name__} : {e}')


# Backward compatibility alias
GitHubMixinBase = GitHubHTTPClient
