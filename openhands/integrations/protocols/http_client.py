"""HTTP Client Protocol for Git Service Integrations."""

from typing import Any, Protocol, runtime_checkable

from pydantic import SecretStr

from openhands.integrations.service_types import RequestMethod, User


@runtime_checkable
class HTTPClient(Protocol):
    """Protocol defining the HTTP client interface for Git service integrations.

    This protocol abstracts the common HTTP client functionality needed by all
    Git service providers (GitHub, GitLab, BitBucket) to enable composition
    over inheritance patterns.
    """

    # Required attributes
    token: SecretStr
    refresh: bool
    external_auth_id: str | None
    base_domain: str | None

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
        ...
