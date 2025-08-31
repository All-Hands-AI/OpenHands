from typing import Any

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    RequestMethod,
    UnknownException,
    User,
)


class GitLabHTTPClient:
    """
    HTTP client implementation for GitLab API operations.
    Implements HTTPClientInterface and provides common functionality for GitLab API interactions.
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
        """Initialize the GitLab HTTP client with configuration."""
        # Set default values
        self.BASE_URL = 'https://gitlab.com/api/v4'
        self.GRAPHQL_URL = 'https://gitlab.com/api/graphql'
        self.token = token or SecretStr('')
        self.refresh = False
        self.external_auth_id = external_auth_id
        self.base_domain = base_domain

        # Handle custom domain configuration
        if base_domain:
            # Check if protocol is already included
            if base_domain.startswith(('http://', 'https://')):
                # Use the provided protocol
                self.BASE_URL = f'{base_domain}/api/v4'
                self.GRAPHQL_URL = f'{base_domain}/api/graphql'
            else:
                # Default to https if no protocol specified
                self.BASE_URL = f'https://{base_domain}/api/v4'
                self.GRAPHQL_URL = f'https://{base_domain}/api/graphql'

    async def _get_headers(self) -> dict:
        """Retrieve the GitLab Token to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
        }

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
                response_headers = {}
                if 'Link' in response.headers:
                    response_headers['Link'] = response.headers['Link']

                if 'X-Total' in response.headers:
                    response_headers['X-Total'] = response.headers['X-Total']

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json(), response_headers
                else:
                    return response.text, response_headers

        except httpx.HTTPStatusError as e:
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if variables is None:
            variables = {}
        try:
            async with httpx.AsyncClient() as client:
                headers = await self._get_headers()
                # Add content type header for GraphQL
                headers['Content-Type'] = 'application/json'

                payload = {
                    'query': query,
                    'variables': variables if variables is not None else {},
                }

                response = await client.post(
                    self.GRAPHQL_URL, headers=headers, json=payload
                )

                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    headers = await self._get_headers()
                    headers['Content-Type'] = 'application/json'
                    response = await client.post(
                        self.GRAPHQL_URL, headers=headers, json=payload
                    )

                response.raise_for_status()
                result = response.json()

                # Check for GraphQL errors
                if 'errors' in result:
                    error_message = result['errors'][0].get(
                        'message', 'Unknown GraphQL error'
                    )
                    raise UnknownException(f'GraphQL error: {error_message}')

                return result.get('data')
        except httpx.HTTPStatusError as e:
            raise self._handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self._handle_http_error(e)

    async def verify_access(self) -> bool:
        url = f'{self.BASE_URL}'
        await self._make_request(url)
        return True

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        response, _ = await self._make_request(url)

        # Use a default avatar URL if not provided
        # In some self-hosted GitLab instances, the avatar_url field may be returned as None.
        avatar_url = response.get('avatar_url') or ''

        return User(
            id=str(response.get('id', '')),
            login=response.get('username'),  # type: ignore[call-arg]
            avatar_url=avatar_url,
            name=response.get('name'),
            email=response.get('email'),
            company=response.get('organization'),
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

            return AuthenticationError('Invalid GitLab token')
        elif e.response.status_code == 404:
            from openhands.integrations.service_types import ResourceNotFoundError

            return ResourceNotFoundError(f'Resource not found on GitLab API: {e}')
        elif e.response.status_code == 429:
            from openhands.integrations.service_types import RateLimitError

            return RateLimitError('GitLab API rate limit exceeded')

        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'Unknown error: {e}')

    def _handle_http_error(self, e: httpx.HTTPError):
        """Handle HTTP errors."""
        from openhands.integrations.service_types import UnknownException

        return UnknownException(f'HTTP error {type(e).__name__} : {e}')
