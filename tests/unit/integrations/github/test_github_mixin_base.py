"""Unit tests for GitHubMixinBase class."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.github.service.base import GitHubMixinBase
from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
    User,
)


class TestableGitHubMixinBase(GitHubMixinBase):
    """Testable implementation of GitHubMixinBase for unit testing."""

    def __init__(self, token: SecretStr | None = None, refresh: bool = False):
        self.token = token or SecretStr('')
        self.refresh = refresh
        self.external_auth_id = None
        self.external_auth_token = None
        self.external_token_manager = False
        self.base_domain = None
        self.BASE_URL = 'https://api.github.com'
        self.GRAPHQL_URL = 'https://api.github.com/graphql'

    @property
    def provider(self) -> str:
        return 'github'

    # Implement abstract methods from BaseGitService
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        return f'{self.BASE_URL}/repos/{repository}/contents/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        return f'{self.BASE_URL}/repos/{repository}/contents/{microagents_path}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request."""
        return None

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return item.get('type') == 'file' and item.get('name', '').endswith('.md')

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        return item.get('name', '')

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return item.get('path', '')


@pytest.mark.asyncio
class TestGitHubMixinBase:
    """Test cases for GitHubMixinBase class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token = SecretStr('test-token')
        self.mixin = TestableGitHubMixinBase(token=self.token)

    async def test_get_headers_with_token(self):
        """Test _get_headers method with valid token."""
        headers = await self.mixin._get_headers()

        assert headers['Authorization'] == 'Bearer test-token'
        assert headers['Accept'] == 'application/vnd.github.v3+json'

    async def test_get_headers_without_token(self):
        """Test _get_headers method without token."""
        mixin = TestableGitHubMixinBase()
        headers = await mixin._get_headers()

        assert headers['Authorization'] == 'Bearer '
        assert headers['Accept'] == 'application/vnd.github.v3+json'

    async def test_get_headers_with_token_refresh(self):
        """Test _get_headers method with token refresh."""
        mixin = TestableGitHubMixinBase()

        # Mock get_latest_token to return a token
        with patch.object(
            mixin, 'get_latest_token', return_value=SecretStr('refreshed-token')
        ):
            headers = await mixin._get_headers()

            assert headers['Authorization'] == 'Bearer refreshed-token'
            assert mixin.token.get_secret_value() == 'refreshed-token'

    async def test_get_latest_token(self):
        """Test get_latest_token method."""
        result = await self.mixin.get_latest_token()

        assert isinstance(result, SecretStr)
        assert result.get_secret_value() == 'test-token'

    async def test_make_request_success(self):
        """Test successful _make_request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'test-user'}
        mock_response.headers = {'Link': 'next-page-link'}
        mock_response.raise_for_status = Mock()

        with patch.object(
            self.mixin, 'execute_request', return_value=mock_response
        ) as mock_execute:
            result, headers = await self.mixin._make_request(
                'https://api.github.com/user'
            )

            assert result == {'login': 'test-user'}
            assert headers == {'Link': 'next-page-link'}
            mock_execute.assert_called_once()

    async def test_make_request_post_method(self):
        """Test _make_request with POST method."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'created': True}
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        with patch.object(
            self.mixin, 'execute_request', return_value=mock_response
        ) as mock_execute:
            result, headers = await self.mixin._make_request(
                'https://api.github.com/repos/owner/repo/issues',
                params={'title': 'Test Issue'},
                method=RequestMethod.POST,
            )

            assert result == {'created': True}
            assert headers == {}
            mock_execute.assert_called_once()

    async def test_make_request_with_token_refresh(self):
        """Test _make_request with token refresh on 401."""
        mixin = TestableGitHubMixinBase(token=self.token, refresh=True)

        # First response returns 401, second response succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status = Mock()

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'login': 'test-user'}
        mock_response_200.headers = {}
        mock_response_200.raise_for_status = Mock()

        with patch.object(
            mixin, 'execute_request', side_effect=[mock_response_401, mock_response_200]
        ) as mock_execute:
            with patch.object(
                mixin, 'get_latest_token', return_value=SecretStr('new-token')
            ):
                result, headers = await mixin._make_request(
                    'https://api.github.com/user'
                )

                assert result == {'login': 'test-user'}
                assert mock_execute.call_count == 2

    async def test_make_request_http_status_error(self):
        """Test _make_request with HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            message='404 Not Found', request=Mock(), response=mock_response
        )
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ResourceNotFoundError):
                await self.mixin._make_request('https://api.github.com/nonexistent')

    async def test_make_request_http_error(self):
        """Test _make_request with general HTTP error."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError('Connection failed')
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(UnknownException):
                await self.mixin._make_request('https://api.github.com/user')

    async def test_execute_graphql_query_success(self):
        """Test successful GraphQL query execution."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'viewer': {'login': 'test-user'}}}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            query = 'query { viewer { login } }'
            variables = {'var1': 'value1'}

            result = await self.mixin.execute_graphql_query(query, variables)

            assert result == {'data': {'viewer': {'login': 'test-user'}}}
            mock_client.post.assert_called_once_with(
                self.mixin.GRAPHQL_URL,
                headers={
                    'Authorization': 'Bearer test-token',
                    'Accept': 'application/vnd.github.v3+json',
                },
                json={'query': query, 'variables': variables},
            )

    async def test_execute_graphql_query_with_errors(self):
        """Test GraphQL query execution with errors in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'errors': [{'message': 'Field not found'}]}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            query = 'query { invalidField }'
            variables = {}

            with pytest.raises(UnknownException) as exc_info:
                await self.mixin.execute_graphql_query(query, variables)

            assert 'GraphQL query error' in str(exc_info.value)

    async def test_execute_graphql_query_http_error(self):
        """Test GraphQL query execution with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            message='401 Unauthorized', request=Mock(), response=mock_response
        )
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(AuthenticationError):
                await self.mixin.execute_graphql_query('query { viewer { login } }', {})

    async def test_verify_access_success(self):
        """Test successful access verification."""
        with patch.object(self.mixin, '_make_request', return_value=({}, {})):
            result = await self.mixin.verify_access()
            assert result is True

    async def test_verify_access_failure(self):
        """Test access verification failure."""
        with patch.object(
            self.mixin,
            '_make_request',
            side_effect=AuthenticationError('Invalid token'),
        ):
            with pytest.raises(AuthenticationError):
                await self.mixin.verify_access()

    async def test_get_user_success(self):
        """Test successful user retrieval."""
        user_data = {
            'id': 12345,
            'login': 'testuser',
            'avatar_url': 'https://github.com/images/error/testuser_happy.gif',
            'company': 'Test Company',
            'name': 'Test User',
            'email': 'test@example.com',
        }

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == '12345'
            assert user.login == 'testuser'
            assert (
                user.avatar_url == 'https://github.com/images/error/testuser_happy.gif'
            )
            assert user.company == 'Test Company'
            assert user.name == 'Test User'
            assert user.email == 'test@example.com'

    async def test_get_user_with_missing_fields(self):
        """Test user retrieval with missing optional fields."""
        user_data = {'id': 12345, 'login': 'testuser'}

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == '12345'
            assert user.login == 'testuser'
            assert user.avatar_url == ''
            assert user.company is None
            assert user.name is None
            assert user.email is None

    async def test_get_user_with_none_values(self):
        """Test user retrieval with None values."""
        user_data = {
            'id': 12345,
            'login': None,
            'avatar_url': None,
            'company': None,
            'name': None,
            'email': None,
        }

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == '12345'
            assert user.login == ''
            assert user.avatar_url == ''
            assert user.company is None
            assert user.name is None
            assert user.email is None

    def test_has_token_expired(self):
        """Test token expiration detection."""
        assert self.mixin._has_token_expired(401) is True
        assert self.mixin._has_token_expired(200) is False
        assert self.mixin._has_token_expired(404) is False
        assert self.mixin._has_token_expired(500) is False

    async def test_execute_request_get(self):
        """Test execute_request with GET method."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_client.get.return_value = mock_response

        url = 'https://api.github.com/user'
        headers = {'Authorization': 'Bearer token'}
        params = {'per_page': 10}

        result = await self.mixin.execute_request(
            mock_client, url, headers, params, RequestMethod.GET
        )

        assert result == mock_response
        mock_client.get.assert_called_once_with(url, headers=headers, params=params)

    async def test_execute_request_post(self):
        """Test execute_request with POST method."""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_client.post.return_value = mock_response

        url = 'https://api.github.com/repos/owner/repo/issues'
        headers = {'Authorization': 'Bearer token'}
        params = {'title': 'Test Issue'}

        result = await self.mixin.execute_request(
            mock_client, url, headers, params, RequestMethod.POST
        )

        assert result == mock_response
        mock_client.post.assert_called_once_with(url, headers=headers, json=params)

    def test_handle_http_status_error_401(self):
        """Test handling of 401 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 401

        error = httpx.HTTPStatusError(
            message='401 Unauthorized', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, AuthenticationError)
        assert 'Invalid github token' in str(result)

    def test_handle_http_status_error_404(self):
        """Test handling of 404 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError(
            message='404 Not Found', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, ResourceNotFoundError)
        assert 'Resource not found on github API' in str(result)

    def test_handle_http_status_error_429(self):
        """Test handling of 429 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 429

        error = httpx.HTTPStatusError(
            message='429 Too Many Requests', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, RateLimitError)
        assert 'github API rate limit exceeded' in str(result)

    def test_handle_http_status_error_other(self):
        """Test handling of other HTTP status errors."""
        mock_response = Mock()
        mock_response.status_code = 500

        error = httpx.HTTPStatusError(
            message='500 Internal Server Error', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, UnknownException)
        assert 'Unknown error' in str(result)

    def test_handle_http_error(self):
        """Test handling of general HTTP errors."""
        error = httpx.ConnectError('Connection failed')

        result = self.mixin.handle_http_error(error)
        assert isinstance(result, UnknownException)
        assert 'HTTP error ConnectError' in str(result)

    def test_provider_property(self):
        """Test provider property."""
        assert self.mixin.provider == 'github'

    async def test_integration_full_request_cycle(self):
        """Test full request cycle integration."""
        # Mock a complete request/response cycle
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'testuser', 'id': 12345}
        mock_response.headers = {'X-RateLimit-Remaining': '4999'}
        mock_response.raise_for_status = Mock()

        with patch.object(
            self.mixin, 'execute_request', return_value=mock_response
        ) as mock_execute:
            # Test the full cycle: headers -> request -> response parsing
            headers = await self.mixin._get_headers()
            result, response_headers = await self.mixin._make_request(
                'https://api.github.com/user'
            )

            # Verify headers were constructed correctly
            assert 'Bearer test-token' in headers['Authorization']

            # Verify request was made with correct parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'

            # Verify response was parsed correctly
            assert result == {'login': 'testuser', 'id': 12345}
            # The _make_request method only extracts 'Link' header, not all headers
            assert response_headers == {}
