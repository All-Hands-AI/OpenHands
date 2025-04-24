import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.provider import ProviderType
from openhands.integrations.utils import validate_provider_token


@pytest.mark.asyncio
async def test_github_sso_token_validation():
    # Mock a response that would come from GitHub when using an SSO token
    class MockResponse:
        def __init__(self, status_code, headers):
            self.status_code = status_code
            self.headers = headers

    class MockHTTPError(httpx.HTTPStatusError):
        def __init__(self, response):
            self.response = response

    # Test case 1: Valid token with SSO
    with pytest.raises(Exception) as exc_info:
        # This will raise an exception that we'll catch and inspect
        await validate_provider_token(SecretStr("test-sso-token"))

    # If the exception is an HTTPStatusError with a 403 and SSO headers,
    # it should still be considered a valid GitHub token
    if isinstance(exc_info.value, httpx.HTTPStatusError):
        response = exc_info.value.response
        if response.status_code == 403 and "X-GitHub-SSO" in response.headers:
            assert True  # Test passed
            return

    # If we get here, the test failed
    assert False, "SSO token validation did not handle the SSO case correctly"
