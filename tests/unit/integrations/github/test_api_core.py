import pytest
from pydantic import SecretStr

from openhands.integrations.github.service.api import GitHubAPI


@pytest.mark.asyncio
async def test_base_urls_github_com():
    api = GitHubAPI(base_domain=None, token=SecretStr("t"))
    assert api.rest_base == "https://api.github.com"
    assert api.graphql_base == "https://api.github.com/graphql"


@pytest.mark.asyncio
async def test_base_urls_enterprise():
    api = GitHubAPI(base_domain="gh.example.com", token=SecretStr("t"))
    assert api.rest_base == "https://gh.example.com/api/v3"
    assert api.graphql_base == "https://gh.example.com/api/graphql"


@pytest.mark.asyncio
async def test_headers_include_standard_and_auth():
    api = GitHubAPI(base_domain=None, token=SecretStr("t"))
    h = api.headers
    assert h["Accept"].startswith("application/vnd.github+")
    assert h["User-Agent"].startswith("OpenHands-GitHubService")
    assert h["X-GitHub-Api-Version"]
    assert h["Authorization"] == "Bearer t"

    api.set_token(None)
    h2 = api.headers
    assert "Authorization" not in h2
