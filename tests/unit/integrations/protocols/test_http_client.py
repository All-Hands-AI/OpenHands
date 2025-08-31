"""Unit tests for HTTPClient protocol."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.protocols.http_client import HTTPClient
from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
    User,
)


class TestableHTTPClient:
    """Testable implementation of HTTPClient protocol for unit testing."""

    def __init__(self, provider_name: str = 'test-provider'):
        self.token = SecretStr('test-token')
        self.refresh = False
        self.external_auth_id = None
        self.external_auth_token = None
        self.external_token_manager = False
        self.base_domain = None
        self._provider_name = provider_name

    @property
    def provider(self) -> str:
        return self._provider_name

    async def get_latest_token(self) -> SecretStr | None:
        return self.token

    async def _get_headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.token.get_secret_value()}'}

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ):
        # Mock implementation for testing
        return {'test': 'data'}, {}

    async def get_user(self) -> User:
        return User(id='123', login='testuser', avatar_url='')


@pytest.mark.asyncio
class TestHTTPClient:
    """Test cases for HTTPClient protocol."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestableHTTPClient()

    def test_default_attributes(self):
        """Test default attribute values."""
        assert isinstance(self.client.token, SecretStr)
        assert self.client.refresh is False
        assert self.client.external_auth_id is None
        assert self.client.external_auth_token is None
        assert self.client.external_token_manager is False
        assert self.client.base_domain is None

    def test_provider_property(self):
        """Test provider property."""
        assert self.client.provider == 'test-provider'

    def test_has_token_expired_default_implementation(self):
        """Test default _has_token_expired implementation."""
        # Create a client that uses the protocol's default implementation
        TestableHTTPClient()

        # The protocol provides a default implementation
        protocol_client = HTTPClient()

        assert protocol_client._has_token_expired(401) is True
        assert protocol_client._has_token_expired(200) is False
        assert protocol_client._has_token_expired(404) is False
        assert protocol_client._has_token_expired(500) is False

    async def test_execute_request_get(self):
        """Test execute_request with GET method."""
        protocol_client = HTTPClient()

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_client.get.return_value = mock_response

        url = 'https://api.example.com/user'
        headers = {'Authorization': 'Bearer token'}
        params = {'per_page': 10}

        result = await protocol_client.execute_request(
            mock_client, url, headers, params, RequestMethod.GET
        )

        assert result == mock_response
        mock_client.get.assert_called_once_with(url, headers=headers, params=params)

    async def test_execute_request_post(self):
        """Test execute_request with POST method."""
        protocol_client = HTTPClient()

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_client.post.return_value = mock_response

        url = 'https://api.example.com/issues'
        headers = {'Authorization': 'Bearer token'}
        params = {'title': 'Test Issue'}

        result = await protocol_client.execute_request(
            mock_client, url, headers, params, RequestMethod.POST
        )

        assert result == mock_response
        mock_client.post.assert_called_once_with(url, headers=headers, json=params)

    def test_handle_http_status_error_401(self):
        """Test handling of 401 HTTP status error."""
        TestableHTTPClient('github')
        protocol_client = HTTPClient()
        protocol_client.provider = 'github'

        mock_response = Mock()
        mock_response.status_code = 401

        error = httpx.HTTPStatusError(
            message='401 Unauthorized', request=Mock(), response=mock_response
        )

        result = protocol_client.handle_http_status_error(error)
        assert isinstance(result, AuthenticationError)
        assert 'Invalid github token' in str(result)

    def test_handle_http_status_error_404(self):
        """Test handling of 404 HTTP status error."""
        protocol_client = HTTPClient()
        protocol_client.provider = 'gitlab'

        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError(
            message='404 Not Found', request=Mock(), response=mock_response
        )

        result = protocol_client.handle_http_status_error(error)
        assert isinstance(result, ResourceNotFoundError)
        assert 'Resource not found on gitlab API' in str(result)

    def test_handle_http_status_error_429(self):
        """Test handling of 429 HTTP status error."""
        protocol_client = HTTPClient()
        protocol_client.provider = 'bitbucket'

        mock_response = Mock()
        mock_response.status_code = 429

        error = httpx.HTTPStatusError(
            message='429 Too Many Requests', request=Mock(), response=mock_response
        )

        result = protocol_client.handle_http_status_error(error)
        assert isinstance(result, RateLimitError)
        assert 'bitbucket API rate limit exceeded' in str(result)

    def test_handle_http_status_error_other(self):
        """Test handling of other HTTP status errors."""
        protocol_client = HTTPClient()
        protocol_client.provider = 'test-provider'

        mock_response = Mock()
        mock_response.status_code = 500

        error = httpx.HTTPStatusError(
            message='500 Internal Server Error', request=Mock(), response=mock_response
        )

        result = protocol_client.handle_http_status_error(error)
        assert isinstance(result, UnknownException)
        assert 'Unknown error' in str(result)

    def test_handle_http_error(self):
        """Test handling of general HTTP errors."""
        protocol_client = HTTPClient()
        protocol_client.provider = 'test-provider'

        error = httpx.ConnectError('Connection failed')

        result = protocol_client.handle_http_error(error)
        assert isinstance(result, UnknownException)
        assert 'HTTP error ConnectError' in str(result)

    def test_handle_http_error_with_different_error_types(self):
        """Test handling of different HTTP error types."""
        protocol_client = HTTPClient()
        protocol_client.provider = 'test-provider'

        # Test with different error types
        errors = [
            httpx.ConnectError('Connection failed'),
            httpx.TimeoutException('Request timed out'),
            httpx.ReadTimeout('Read timeout'),
            httpx.WriteTimeout('Write timeout'),
        ]

        for error in errors:
            result = protocol_client.handle_http_error(error)
            assert isinstance(result, UnknownException)
            assert f'HTTP error {type(error).__name__}' in str(result)

    def test_runtime_checkable(self):
        """Test that HTTPClient is runtime checkable."""
        from openhands.integrations.protocols.http_client import HTTPClient

        # Test that our testable client implements the protocol
        assert isinstance(self.client, HTTPClient)

        # Test that a class without the required methods doesn't implement the protocol
        class IncompleteClient:
            pass

        incomplete = IncompleteClient()
        assert not isinstance(incomplete, HTTPClient)

    def test_protocol_attributes_exist(self):
        """Test that protocol defines expected attributes."""
        protocol_client = HTTPClient()

        # Test default attribute values from protocol
        assert hasattr(protocol_client, 'token')
        assert hasattr(protocol_client, 'refresh')
        assert hasattr(protocol_client, 'external_auth_id')
        assert hasattr(protocol_client, 'external_auth_token')
        assert hasattr(protocol_client, 'external_token_manager')
        assert hasattr(protocol_client, 'base_domain')

        # Test default values
        assert protocol_client.token == SecretStr('')
        assert protocol_client.refresh is False
        assert protocol_client.external_auth_id is None
        assert protocol_client.external_auth_token is None
        assert protocol_client.external_token_manager is False
        assert protocol_client.base_domain is None

    def test_protocol_methods_exist(self):
        """Test that protocol defines expected methods."""
        protocol_client = HTTPClient()

        # Test that methods exist
        assert hasattr(protocol_client, 'get_latest_token')
        assert hasattr(protocol_client, '_get_headers')
        assert hasattr(protocol_client, '_make_request')
        assert hasattr(protocol_client, 'get_user')
        assert hasattr(protocol_client, '_has_token_expired')
        assert hasattr(protocol_client, 'execute_request')
        assert hasattr(protocol_client, 'handle_http_status_error')
        assert hasattr(protocol_client, 'handle_http_error')
        assert hasattr(protocol_client, 'provider')

    async def test_protocol_abstract_methods_raise_not_implemented(self):
        """Test that abstract protocol methods raise NotImplementedError."""
        protocol_client = HTTPClient()

        # These methods should raise NotImplementedError when called on the protocol directly
        with pytest.raises((NotImplementedError, AttributeError)):
            await protocol_client.get_latest_token()

        with pytest.raises((NotImplementedError, AttributeError)):
            await protocol_client._get_headers()

        with pytest.raises((NotImplementedError, AttributeError)):
            await protocol_client._make_request('http://example.com')

        with pytest.raises((NotImplementedError, AttributeError)):
            await protocol_client.get_user()

        with pytest.raises((NotImplementedError, AttributeError)):
            _ = protocol_client.provider

    def test_provider_specific_error_messages(self):
        """Test that error messages are provider-specific."""
        providers = ['github', 'gitlab', 'bitbucket']

        for provider in providers:
            protocol_client = HTTPClient()
            protocol_client.provider = provider

            # Test 401 error
            mock_response = Mock()
            mock_response.status_code = 401
            error = httpx.HTTPStatusError(
                message='401 Unauthorized', request=Mock(), response=mock_response
            )
            result = protocol_client.handle_http_status_error(error)
            assert f'Invalid {provider} token' in str(result)

            # Test 404 error
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                message='404 Not Found', request=Mock(), response=mock_response
            )
            result = protocol_client.handle_http_status_error(error)
            assert f'Resource not found on {provider} API' in str(result)

            # Test 429 error
            mock_response.status_code = 429
            error = httpx.HTTPStatusError(
                message='429 Too Many Requests', request=Mock(), response=mock_response
            )
            result = protocol_client.handle_http_status_error(error)
            assert f'{provider} API rate limit exceeded' in str(result)

    def test_protocol_composition_over_inheritance(self):
        """Test that the protocol enables composition over inheritance."""
        # This test demonstrates that classes can implement HTTPClient
        # without inheriting from a base class

        class ComposedService:
            def __init__(self):
                self.token = SecretStr('composed-token')
                self.refresh = True
                self.external_auth_id = 'external-id'
                self.external_auth_token = SecretStr('external-token')
                self.external_token_manager = True
                self.base_domain = 'example.com'

            @property
            def provider(self) -> str:
                return 'composed-provider'

            async def get_latest_token(self) -> SecretStr | None:
                return self.token

            async def _get_headers(self) -> dict[str, str]:
                return {'Authorization': f'Bearer {self.token.get_secret_value()}'}

            async def _make_request(
                self,
                url: str,
                params: dict | None = None,
                method: RequestMethod = RequestMethod.GET,
            ):
                return {'composed': True}, {}

            async def get_user(self) -> User:
                return User(id='composed-123', login='composed-user', avatar_url='')

        service = ComposedService()

        # Verify it implements the protocol
        assert isinstance(service, HTTPClient)

        # Verify it has all the expected attributes and methods
        assert service.provider == 'composed-provider'
        assert service.token.get_secret_value() == 'composed-token'
        assert service.refresh is True
        assert service.external_auth_id == 'external-id'
        assert service.external_token_manager is True
        assert service.base_domain == 'example.com'
