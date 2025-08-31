from typing import Any, Protocol

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import RequestMethod, User

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from httpx import AsyncClient, HTTPError, HTTPStatusError
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.microagent.microagent import BaseMicroagent
from openhands.microagent.types import MicroagentContentResponse, MicroagentResponse
from openhands.server.types import AppMode


class AuthenticationError(ValueError):
    """Raised when there is an issue with GitHub authentication."""

    pass


class UnknownException(ValueError):
    """Raised when there is an issue with GitHub communcation."""

    pass



class RateLimitError(ValueError):
    """Raised when the git provider's API rate limits are exceeded."""

    pass


class ResourceNotFoundError(ValueError):
    """Raised when a requested resource (file, directory, etc.) is not found."""

    pass


class HTTPClientProtocol(Protocol):
    """Protocol defining the HTTP client interface for Git service operations."""

    BASE_URL: str
    GRAPHQL_URL: str | None
    token: SecretStr
    refresh: bool
    external_auth_id: str | None
    base_domain: str | None

    @property
    def provider(self) -> str:
        raise NotImplementedError('Subclasses must implement the provider property')


    @abstractmethod
    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]: ...


    async def _get_headers(self) -> dict:
        """Retrieve the token from settings store to construct the headers."""
        ...

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user."""
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

    async def execute_request(
        self,
        client: AsyncClient,
        url: str,
        headers: dict,
        params: dict | None,
        method: RequestMethod = RequestMethod.GET,
    ):
        if method == RequestMethod.POST:
            return await client.post(url, headers=headers, json=params)
        return await client.get(url, headers=headers, params=params)

    def handle_http_status_error(
        self, e: HTTPStatusError
    ) -> (
        AuthenticationError | RateLimitError | ResourceNotFoundError | UnknownException
    ):
        if e.response.status_code == 401:
            return AuthenticationError(f'Invalid {self.provider} token')
        elif e.response.status_code == 404:
            return ResourceNotFoundError(
                f'Resource not found on {self.provider} API: {e}'
            )
        elif e.response.status_code == 429:
            logger.warning(f'Rate limit exceeded on {self.provider} API: {e}')
            return RateLimitError('GitHub API rate limit exceeded')

        logger.warning(f'Status error on {self.provider} API: {e}')
        return UnknownException(f'Unknown error: {e}')


    def handle_http_error(self, e: HTTPError) -> UnknownException:
        logger.warning(f'HTTP error on {self.provider} API: {type(e).__name__} : {e}')
        return UnknownException(f'HTTP error {type(e).__name__} : {e}')
