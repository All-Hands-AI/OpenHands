import base64
from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    RequestMethod,
    User,
)


class BitBucketHTTPClient:
    """
    HTTP client implementation for Bitbucket API operations.
    Implements HTTPClientInterface and provides common functionality for Bitbucket API interactions.
    """

    BASE_URL: str
    GRAPHQL_URL: str | None
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
        """Initialize the Bitbucket HTTP client with configuration."""
        # Set default values
        self.BASE_URL = 'https://api.bitbucket.org/2.0'
        self.GRAPHQL_URL = None  # Bitbucket doesn't have GraphQL API
        self.token = token or SecretStr('')
        self.refresh = False
        self.external_auth_id = external_auth_id
        self.base_domain = base_domain or 'bitbucket.org'

        # Handle custom domain configuration
        if base_domain:
            self.BASE_URL = f'https://api.{base_domain}/2.0'

    async def _get_headers(self) -> dict[str, str]:
        """Get headers for Bitbucket API requests."""
        token_value = self.token.get_secret_value()

        # Check if the token contains a colon, which indicates it's in username:password format
        if ':' in token_value:
            auth_str = base64.b64encode(token_value.encode()).decode()
            return {
                'Authorization': f'Basic {auth_str}',
                'Accept': 'application/json',
            }
        else:
            return {
                'Authorization': f'Bearer {token_value}',
                'Accept': 'application/json',
            }

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user."""
        return self.token

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make a request to the Bitbucket API.

        Args:
            url: The URL to request
            params: Optional parameters for the request
            method: The HTTP method to use

        Returns:
            A tuple of (response_data, response_headers)

        """
        try:
            async with httpx.AsyncClient() as client:
                headers = await self._get_headers()
                response = await self._execute_request(
                    client, url, headers, params, method
                )
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
                return response.json(), dict(response.headers)
        except httpx.HTTPStatusError as e:
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the API."""
        # Bitbucket doesn't support GraphQL
        raise NotImplementedError("Bitbucket doesn't support GraphQL")

    async def verify_access(self) -> bool:
        """Verify that the client has access to the API."""
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True

    async def get_user(self) -> User:
        """Get the authenticated user's information."""
        url = f'{self.BASE_URL}/user'
        data, _ = await self._make_request(url)

        account_id = data.get('account_id', '')

        return User(
            id=account_id,
            login=data.get('username', ''),
            avatar_url=data.get('links', {}).get('avatar', {}).get('href', ''),
            name=data.get('display_name'),
            email=None,  # Bitbucket API doesn't return email in this endpoint
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

            return AuthenticationError('Invalid Bitbucket token')
        elif e.response.status_code == 404:
            from openhands.integrations.service_types import ResourceNotFoundError

            return ResourceNotFoundError(f'Resource not found on Bitbucket API: {e}')
        elif e.response.status_code == 429:
            from openhands.integrations.service_types import RateLimitError

            return RateLimitError('Bitbucket API rate limit exceeded')

        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'Unknown error: {e}')

    def _handle_http_error(self, e: httpx.HTTPError):
        """Handle HTTP errors."""
        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'HTTP error {type(e).__name__} : {e}')
