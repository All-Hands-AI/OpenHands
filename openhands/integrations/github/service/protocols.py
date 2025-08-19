from typing import Any, Protocol

from httpx import HTTPError, HTTPStatusError
from pydantic import SecretStr

from openhands.integrations.service_types import (
    MicroagentContentResponse,
    Repository,
    RequestMethod,
    User,
)


class GitHubServiceProtocol(Protocol):
    BASE_URL: str
    token: SecretStr
    refresh: bool
    external_auth_id: str | None

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]: ...

    async def get_user(self) -> User: ...

    def _parse_repository(
        self, repo: dict, link_header: str | None = None
    ) -> Repository: ...

    async def get_installations(self) -> list[str]: ...

    async def _get_github_headers(self) -> dict: ...

    def handle_http_status_error(self, e: HTTPStatusError) -> Exception: ...

    def handle_http_error(self, e: HTTPError) -> Exception: ...

    def _parse_microagent_content(
        self, content: str, file_path: str
    ) -> MicroagentContentResponse: ...
