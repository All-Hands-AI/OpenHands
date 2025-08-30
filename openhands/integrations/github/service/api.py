from __future__ import annotations

import asyncio
import random
from typing import Any, Mapping

import httpx
from pydantic import SecretStr

from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
)


class GitHubAPI:
    """
    Thin HTTP/GraphQL wrapper for GitHub with correct base URLs, standard headers,
    shared AsyncClient, and basic retry/backoff for 429/5xx.

    This component is internal. It does not alter existing behavior until wired
    into GitHubService/mixins in subsequent PRs.
    """

    def __init__(
        self,
        *,
        base_domain: str | None = None,
        token: SecretStr | None = None,
        user_agent: str = "OpenHands-GitHubService",
        timeout: float = 15.0,
    ) -> None:
        domain = (base_domain or "github.com").strip()
        if domain == "github.com":
            self.rest_base = "https://api.github.com"
            self.graphql_base = "https://api.github.com/graphql"
        else:
            self.rest_base = f"https://{domain}/api/v3"
            self.graphql_base = f"https://{domain}/api/graphql"

        self._token = token.get_secret_value() if token else ""
        # Shared client for all requests through this API instance
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

        # Standard headers recommended by GitHub
        self._base_headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "User-Agent": user_agent,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            self._base_headers["Authorization"] = f"Bearer {self._token}"

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubAPI":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()

    def set_token(self, token: SecretStr | None) -> None:
        self._token = token.get_secret_value() if token else ""
        if self._token:
            self._base_headers["Authorization"] = f"Bearer {self._token}"
        elif "Authorization" in self._base_headers:
            del self._base_headers["Authorization"]

    @property
    def headers(self) -> Mapping[str, str]:
        return dict(self._base_headers)

    def _full_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url
        return f"{self.rest_base}{path_or_url}"

    async def request(
        self,
        method: RequestMethod | str = RequestMethod.GET,
        path_or_url: str = "/",
        *,
        params: dict | None = None,
        json: dict | None = None,
        extra_headers: Mapping[str, str] | None = None,
        max_retries: int = 2,
        backoff_base: float = 0.25,
    ) -> tuple[Any, dict[str, str]]:
        """
        Perform a REST request with basic retry for 429 and 5xx.
        Returns (json_body, response_headers).
        """
        url = self._full_url(path_or_url)
        headers = {**self._base_headers, **(extra_headers or {})}
        meth = method.value if isinstance(method, RequestMethod) else method.lower()

        attempt = 0
        while True:
            try:
                resp = await self._client.request(meth, url, headers=headers, params=params, json=json)
                # Map errors consistently
                if resp.status_code == 401:
                    raise AuthenticationError("Invalid github token")
                if resp.status_code == 404:
                    raise ResourceNotFoundError(f"Resource not found on GitHub API: {url}")
                if resp.status_code in (429, 500, 502, 503, 504):
                    if attempt < max_retries:
                        delay = backoff_base * (2**attempt) + random.uniform(0, 0.1)
                        attempt += 1
                        await asyncio.sleep(delay)
                        continue
                    raise RateLimitError("GitHub API rate limit or transient error")

                resp.raise_for_status()
                headers_out: dict[str, str] = {}
                # copy interesting headers (Link, RateLimit, etc.) if present
                if "Link" in resp.headers:
                    headers_out["Link"] = resp.headers["Link"]
                if "X-RateLimit-Remaining" in resp.headers:
                    headers_out["X-RateLimit-Remaining"] = resp.headers["X-RateLimit-Remaining"]
                if "X-RateLimit-Reset" in resp.headers:
                    headers_out["X-RateLimit-Reset"] = resp.headers["X-RateLimit-Reset"]
                return resp.json(), headers_out

            except (httpx.HTTPError) as e:  # network errors
                if attempt < max_retries:
                    delay = backoff_base * (2**attempt) + random.uniform(0, 0.1)
                    attempt += 1
                    await asyncio.sleep(delay)
                    continue
                raise UnknownException(f"HTTP error {type(e).__name__}: {e}") from e

    async def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {**self._base_headers, **(extra_headers or {})}
        resp = await self._client.post(
            self.graphql_base,
            headers=headers,
            json={"query": query, "variables": variables or {}},
        )
        if resp.status_code == 401:
            raise AuthenticationError("Invalid github token")
        if resp.status_code == 404:
            raise ResourceNotFoundError("GraphQL endpoint not found")
        if resp.status_code in (429, 500, 502, 503, 504):
            raise RateLimitError("GitHub API rate limit or transient error")
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "errors" in data:
            raise UnknownException(f"GraphQL query error: {data['errors']}")
        if not isinstance(data, dict):
            raise UnknownException("Unexpected GraphQL response type")
        return data
