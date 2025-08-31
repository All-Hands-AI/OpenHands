from typing import Any, Protocol

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import RequestMethod, User


class HTTPClientInterface(Protocol):
    """Protocol defining the HTTP client interface for Git service operations."""

    BASE_URL: str
    GRAPHQL_URL: str | None
    token: SecretStr
    refresh: bool
    external_auth_id: str | None
    base_domain: str | None

    async def _get_headers(self) -> dict:
        """Retrieve the token from settings store to construct the headers."""
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
        """Make an HTTP request to the API."""
        ...

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the API."""
        ...

    async def verify_access(self) -> bool:
        """Verify that the client has access to the API."""
        ...

    async def get_user(self) -> User:
        """Get the authenticated user's information."""
        ...

    def _has_token_expired(self, status_code: int) -> bool:
        """Check if the token has expired based on status code."""
        ...

    async def _execute_request(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        """Execute HTTP request."""
        ...

    def _handle_http_status_error(self, e: httpx.HTTPStatusError):
        """Handle HTTP status errors."""
        ...

    def _handle_http_error(self, e: httpx.HTTPError):
        """Handle HTTP errors."""
        ...
