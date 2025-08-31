"""Unit tests for GitLabMixinBase class."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.gitlab.service.base import GitLabMixinBase
from openhands.integrations.service_types import (
    AuthenticationError,
    RateLimitError,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
    User,
)


class TestableGitLabMixinBase(GitLabMixinBase):
    """Testable implementation of GitLabMixinBase for unit testing."""

    def __init__(self, token: SecretStr | None = None, refresh: bool = False):
        self.token = token or SecretStr('')
        self.refresh = refresh
        self.external_auth_id = None
        self.external_auth_token = None
        self.external_token_manager = False
        self.base_domain = None
        self.BASE_URL = 'https://gitlab.com/api/v4'
        self.GRAPHQL_URL = 'https://gitlab.com/api/graphql'

    @property
    def provider(self) -> str:
        return 'gitlab'

    # Implement abstract methods from BaseGitService
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        project_id = self.extract_project_id(repository)
        return f'{self.BASE_URL}/projects/{project_id}/repository/files/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        project_id = self.extract_project_id(repository)
        return f'{self.BASE_URL}/projects/{project_id}/repository/tree'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request."""
        return {'path': microagents_path, 'recursive': False}

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return item.get('type') == 'blob' and item.get('name', '').endswith('.md')

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        return item.get('name', '')

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return item.get('path', '')


@pytest.mark.asyncio
class TestGitLabMixinBase:
    """Test cases for GitLabMixinBase class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token = SecretStr('test-token')
        self.mixin = TestableGitLabMixinBase(token=self.token)

    async def test_get_headers_with_token(self):
        """Test _get_headers method with valid token."""
        headers = await self.mixin._get_headers()

        assert headers['Authorization'] == 'Bearer test-token'

    async def test_get_headers_without_token(self):
        """Test _get_headers method without token."""
        mixin = TestableGitLabMixinBase()
        headers = await mixin._get_headers()

        assert headers['Authorization'] == 'Bearer '

    async def test_get_headers_with_token_refresh(self):
        """Test _get_headers method with token refresh."""
        mixin = TestableGitLabMixinBase()

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

    async def test_make_request_success_json(self):
        """Test successful _make_request with JSON response."""
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {'username': 'test-user'}
        mock_response.headers = {
            'Link': 'next-page-link',
            'X-Total': '100',
            'Content-Type': 'application/json',
        }
        mock_response.raise_for_status = Mock()

        with patch.object(
            self.mixin, 'execute_request', return_value=mock_response
        ) as mock_execute:
            result, headers = await self.mixin._make_request(
                'https://gitlab.com/api/v4/user'
            )

            assert result == {'username': 'test-user'}
            assert headers == {'Link': 'next-page-link', 'X-Total': '100'}
            mock_execute.assert_called_once()

    async def test_make_request_success_text(self):
        """Test successful _make_request with text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'plain text response'
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            result, headers = await self.mixin._make_request(
                'https://gitlab.com/api/v4/projects/1/raw'
            )

            assert result == 'plain text response'
            assert headers == {}

    async def test_make_request_post_method(self):
        """Test _make_request with POST method."""
        mock_response = Mock()

        mock_response.status_code = 201

        mock_response.json.return_value = {'created': True}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            result, headers = await self.mixin._make_request(
                'https://gitlab.com/api/v4/projects/1/issues',
                params={'title': 'Test Issue'},
                method=RequestMethod.POST,
            )

            assert result == {'created': True}
            mock_client.post.assert_called_once()

    async def test_make_request_with_token_refresh(self):
        """Test _make_request with token refresh on 401."""
        mixin = TestableGitLabMixinBase(token=self.token, refresh=True)

        # First response returns 401, second response succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status = Mock()

        mock_response_200 = Mock()

        mock_response_200.status_code = 200

        mock_response_200.json.return_value = {'username': 'test-user'}
        mock_response_200.headers = {'Content-Type': 'application/json'}
        mock_response_200.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_response_401, mock_response_200]
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch.object(
                mixin, 'get_latest_token', return_value=SecretStr('new-token')
            ):
                result, headers = await mixin._make_request(
                    'https://gitlab.com/api/v4/user'
                )

                assert result == {'username': 'test-user'}
                assert mock_client.get.call_count == 2

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
                await self.mixin._make_request('https://gitlab.com/api/v4/nonexistent')

    async def test_make_request_http_error(self):
        """Test _make_request with general HTTP error."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError('Connection failed')
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(UnknownException):
                await self.mixin._make_request('https://gitlab.com/api/v4/user')

    async def test_execute_graphql_query_success(self):
        """Test successful GraphQL query execution."""
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {
            'data': {'currentUser': {'username': 'test-user'}}
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            query = 'query { currentUser { username } }'
            variables = {'var1': 'value1'}

            result = await self.mixin.execute_graphql_query(query, variables)

            assert result == {'currentUser': {'username': 'test-user'}}
            mock_client.post.assert_called_once_with(
                self.mixin.GRAPHQL_URL,
                headers={
                    'Authorization': 'Bearer test-token',
                    'Content-Type': 'application/json',
                },
                json={'query': query, 'variables': variables},
            )

    async def test_execute_graphql_query_no_variables(self):
        """Test GraphQL query execution without variables."""
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {
            'data': {'currentUser': {'username': 'test-user'}}
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            query = 'query { currentUser { username } }'

            result = await self.mixin.execute_graphql_query(query)

            assert result == {'currentUser': {'username': 'test-user'}}
            # Verify variables defaults to empty dict
            call_args = mock_client.post.call_args
            assert call_args[1]['json']['variables'] == {}

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

            with pytest.raises(UnknownException) as exc_info:
                await self.mixin.execute_graphql_query(query)

            assert 'GraphQL error: Field not found' in str(exc_info.value)

    async def test_execute_graphql_query_with_errors_no_message(self):
        """Test GraphQL query execution with errors but no message."""
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {
            'errors': [{}]  # Error without message
        }
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            query = 'query { invalidField }'

            with pytest.raises(UnknownException) as exc_info:
                await self.mixin.execute_graphql_query(query)

            assert 'GraphQL error: Unknown GraphQL error' in str(exc_info.value)

    async def test_execute_graphql_query_with_token_refresh(self):
        """Test GraphQL query execution with token refresh."""
        mixin = TestableGitLabMixinBase(token=self.token, refresh=True)

        # First response returns 401, second response succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status = Mock()

        mock_response_200 = Mock()

        mock_response_200.status_code = 200

        mock_response_200.json.return_value = {
            'data': {'currentUser': {'username': 'test-user'}}
        }
        mock_response_200.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.side_effect = [mock_response_401, mock_response_200]
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch.object(
                mixin, 'get_latest_token', return_value=SecretStr('new-token')
            ):
                query = 'query { currentUser { username } }'
                result = await mixin.execute_graphql_query(query)

                assert result == {'currentUser': {'username': 'test-user'}}
                assert mock_client.post.call_count == 2

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
                await self.mixin.execute_graphql_query(
                    'query { currentUser { username } }'
                )

    async def test_get_user_success(self):
        """Test successful user retrieval."""
        user_data = {
            'id': 12345,
            'username': 'testuser',
            'avatar_url': 'https://gitlab.com/uploads/-/system/user/avatar/12345/avatar.png',
            'name': 'Test User',
            'email': 'test@example.com',
            'organization': 'Test Org',
        }

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == '12345'
            assert user.login == 'testuser'
            assert (
                user.avatar_url
                == 'https://gitlab.com/uploads/-/system/user/avatar/12345/avatar.png'
            )
            assert user.name == 'Test User'
            assert user.email == 'test@example.com'
            assert user.company == 'Test Org'

    async def test_get_user_with_missing_fields(self):
        """Test user retrieval with missing optional fields."""
        user_data = {'id': 12345, 'username': 'testuser'}

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == '12345'
            assert user.login == 'testuser'
            assert user.avatar_url == ''
            assert user.name is None
            assert user.email is None
            assert user.company is None

    async def test_get_user_with_none_avatar_url(self):
        """Test user retrieval with None avatar_url."""
        user_data = {
            'id': 12345,
            'username': 'testuser',
            'avatar_url': None,
            'name': 'Test User',
            'email': 'test@example.com',
        }

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.avatar_url == ''  # Should default to empty string

    def test_extract_project_id_simple(self):
        """Test _extract_project_id with simple owner/repo format."""
        project_id = self.mixin._extract_project_id('owner/repo')
        assert project_id == 'owner%2Frepo'

    def test_extract_project_id_with_domain(self):
        """Test _extract_project_id with domain/owner/repo format."""
        project_id = self.mixin._extract_project_id('gitlab.example.com/owner/repo')
        assert project_id == 'owner%2Frepo'

    def test_extract_project_id_complex_path(self):
        """Test _extract_project_id with complex path."""
        project_id = self.mixin._extract_project_id(
            'gitlab.example.com/group/subgroup/repo'
        )
        assert project_id == 'group%2Fsubgroup%2Frepo'

    def test_extract_project_id_no_slash(self):
        """Test _extract_project_id with no slash (single name)."""
        project_id = self.mixin._extract_project_id('repo')
        assert project_id == 'repo'

    def test_has_token_expired(self):
        """Test token expiration detection."""
        assert self.mixin._has_token_expired(401) is True
        assert self.mixin._has_token_expired(200) is False
        assert self.mixin._has_token_expired(404) is False
        assert self.mixin._has_token_expired(500) is False

    async def test_execute_request_get(self):
        """Test execute_request with GET method."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_client.get.return_value = mock_response

        url = 'https://gitlab.com/api/v4/user'
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
        mock_response = Mock()
        mock_client.post.return_value = mock_response

        url = 'https://gitlab.com/api/v4/projects/1/issues'
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
        assert 'Invalid gitlab token' in str(result)

    def test_handle_http_status_error_404(self):
        """Test handling of 404 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError(
            message='404 Not Found', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, ResourceNotFoundError)
        assert 'Resource not found on gitlab API' in str(result)

    def test_handle_http_status_error_429(self):
        """Test handling of 429 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 429

        error = httpx.HTTPStatusError(
            message='429 Too Many Requests', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, RateLimitError)
        assert 'gitlab API rate limit exceeded' in str(result)

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
        assert self.mixin.provider == 'gitlab'

    async def test_integration_full_request_cycle(self):
        """Test full request cycle integration."""
        # Mock a complete request/response cycle
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {'username': 'testuser', 'id': 12345}
        mock_response.headers = {'X-Total': '50', 'Content-Type': 'application/json'}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            # Test the full cycle: headers -> request -> response parsing
            headers = await self.mixin._get_headers()
            result, response_headers = await self.mixin._make_request(
                'https://gitlab.com/api/v4/user'
            )

            # Verify headers were constructed correctly
            assert 'Bearer test-token' in headers['Authorization']

            # Verify request was made with correct parameters
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'

            # Verify response was parsed correctly
            assert result == {'username': 'testuser', 'id': 12345}
            assert response_headers == {'X-Total': '50'}
