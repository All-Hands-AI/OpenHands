"""HTTP Client Protocol for Git Service Integrations."""

from typing import Any, Protocol, runtime_checkable

from httpx import AsyncClient, HTTPError, HTTPStatusError
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
    User,
)


@runtime_checkable
class HTTPClient(Protocol):
    """Protocol defining the HTTP client interface for Git service integrations.

    This protocol abstracts the common HTTP client functionality needed by all
    Git service providers (GitHub, GitLab, BitBucket) to enable composition
    over inheritance patterns.
    """

    # Required attributes
    token: SecretStr = SecretStr('')
    refresh: bool = False
    external_auth_id: str | None = None
    external_auth_token: SecretStr | None = None
    external_token_manager: bool = False
    base_domain: str | None = None

    # Required property
    @property
    def provider(self) -> str:
        """Get the provider name for this service."""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get the latest working token for the service.

        Returns:
            The latest token if available, None otherwise
        """
        ...

    async def _get_headers(self) -> dict[str, Any]:
        """Get HTTP headers for API requests.

        This method should construct the appropriate headers including
        authentication for the specific Git service provider.

        Returns:
            Dictionary of HTTP headers
        """
        ...

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """Make an HTTP request to the Git service API.

        Args:
            url: The URL to request
            params: Optional parameters for the request
            method: The HTTP method to use

        Returns:
            A tuple of (response_data, response_headers)
        """
        ...

    async def get_user(self) -> User:
        """Get the authenticated user's information.

        Returns:
            User object with authenticated user details
        """
        ...

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if the token has expired based on HTTP status code.

        Args:
            status_code: HTTP status code from the response

        Returns:
            True if the token has expired, False otherwise
        """
        return status_code == 401

    async def execute_request(
        self,
        client: AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        """Execute an HTTP request using the provided client.

        Args:
            client: The HTTP client to use for the request
            url: The URL to request
            headers: HTTP headers for the request
            params: Optional parameters for the request
            method: The HTTP method to use

        Returns:
            The response from the HTTP request
        """
        if method == RequestMethod.POST:
            return await client.post(url, headers=headers, json=params)
        return await client.get(url, headers=headers, params=params)

    def handle_http_status_error(
        self, e: HTTPStatusError
    ) -> (
        AuthenticationError | RateLimitError | ResourceNotFoundError | UnknownException
    ):
        """Handle HTTP status errors and convert them to appropriate exceptions.

        Args:
            e: The HTTPStatusError to handle

        Returns:
            An appropriate exception based on the status code
        """
        if e.response.status_code == 401:
            return AuthenticationError(f'Invalid {self.provider} token')
        elif e.response.status_code == 404:
            return ResourceNotFoundError(
                f'Resource not found on {self.provider} API: {e}'
            )
        elif e.response.status_code == 429:
            logger.warning(f'Rate limit exceeded on {self.provider} API: {e}')
            # Use generic rate limit message since provider-specific messages
            # would require knowing the specific provider
            return RateLimitError(f'{self.provider} API rate limit exceeded')

        logger.warning(f'Status error on {self.provider} API: {e}')
        return UnknownException(f'Unknown error: {e}')

    def handle_http_error(self, e: HTTPError) -> UnknownException:
        """Handle general HTTP errors.

        Args:
            e: The HTTPError to handle

        Returns:
            An UnknownException wrapping the original error
        """
        logger.warning(f'HTTP error on {self.provider} API: {type(e).__name__} : {e}')
        return UnknownException(f'HTTP error {type(e).__name__} : {e}')
