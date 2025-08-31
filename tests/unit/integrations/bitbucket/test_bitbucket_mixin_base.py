"""Unit tests for BitBucketMixinBase class."""

import base64
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from openhands.integrations.bitbucket.service.base import BitBucketMixinBase
from openhands.integrations.service_types import (
    AuthenticationError,
    OwnerType,
    ProviderType,
    RateLimitError,
    Repository,
    RequestMethod,
    ResourceNotFoundError,
    UnknownException,
    User,
)


class TestableBitBucketMixinBase(BitBucketMixinBase):
    """Testable implementation of BitBucketMixinBase for unit testing."""

    def __init__(self, token: SecretStr | None = None, refresh: bool = False):
        self.token = token or SecretStr('')
        self.refresh = refresh
        self.external_auth_id = None
        self.external_auth_token = None
        self.external_token_manager = False
        self.base_domain = None

    @property
    def provider(self) -> str:
        return 'bitbucket'

    # Implement abstract methods from BaseGitService
    async def _get_cursorrules_url(self, repository: str) -> str:
        """Get the URL for checking .cursorrules file."""
        owner, repo = self._extract_owner_and_repo(repository)
        return f'https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/src/main/.cursorrules'

    async def _get_microagents_directory_url(
        self, repository: str, microagents_path: str
    ) -> str:
        """Get the URL for checking microagents directory."""
        owner, repo = self._extract_owner_and_repo(repository)
        return f'https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/src/main/{microagents_path}'

    def _get_microagents_directory_params(self, microagents_path: str) -> dict | None:
        """Get parameters for the microagents directory request."""
        return None

    def _is_valid_microagent_file(self, item: dict) -> bool:
        """Check if an item represents a valid microagent file."""
        return item.get('type') == 'commit_file' and item.get('path', '').endswith(
            '.md'
        )

    def _get_file_name_from_item(self, item: dict) -> str:
        """Extract file name from directory item."""
        path = item.get('path', '')
        return path.split('/')[-1] if path else ''

    def _get_file_path_from_item(self, item: dict, microagents_path: str) -> str:
        """Extract file path from directory item."""
        return item.get('path', '')


@pytest.mark.asyncio
class TestBitBucketMixinBase:
    """Test cases for BitBucketMixinBase class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token = SecretStr('test-token')
        self.mixin = TestableBitBucketMixinBase(token=self.token)

    def test_extract_owner_and_repo_valid(self):
        """Test _extract_owner_and_repo with valid repository string."""
        owner, repo = self.mixin._extract_owner_and_repo('workspace/repo-name')
        assert owner == 'workspace'
        assert repo == 'repo-name'

    def test_extract_owner_and_repo_complex_path(self):
        """Test _extract_owner_and_repo with complex path."""
        owner, repo = self.mixin._extract_owner_and_repo('domain/workspace/repo-name')
        assert owner == 'workspace'
        assert repo == 'repo-name'

    def test_extract_owner_and_repo_invalid(self):
        """Test _extract_owner_and_repo with invalid repository string."""
        with pytest.raises(ValueError, match='Invalid repository name: repo'):
            self.mixin._extract_owner_and_repo('repo')

    async def test_get_latest_token(self):
        """Test get_latest_token method."""
        result = await self.mixin.get_latest_token()

        assert isinstance(result, SecretStr)
        assert result.get_secret_value() == 'test-token'

    def test_has_token_expired(self):
        """Test token expiration detection."""
        assert self.mixin._has_token_expired(401) is True
        assert self.mixin._has_token_expired(200) is False
        assert self.mixin._has_token_expired(404) is False
        assert self.mixin._has_token_expired(500) is False

    async def test_get_headers_bearer_token(self):
        """Test _get_headers method with Bearer token."""
        headers = await self.mixin._get_headers()

        assert headers['Authorization'] == 'Bearer test-token'
        assert headers['Accept'] == 'application/json'

    async def test_get_headers_basic_auth(self):
        """Test _get_headers method with Basic auth (username:password format)."""
        mixin = TestableBitBucketMixinBase(token=SecretStr('username:password'))
        headers = await mixin._get_headers()

        expected_auth = base64.b64encode('username:password'.encode()).decode()
        assert headers['Authorization'] == f'Basic {expected_auth}'
        assert headers['Accept'] == 'application/json'

    async def test_make_request_success(self):
        """Test successful _make_request."""
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {'username': 'test-user'}
        mock_response.headers = {'X-RateLimit-Remaining': '4999'}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            result, headers = await self.mixin._make_request(
                'https://api.bitbucket.org/2.0/user'
            )

            assert result == {'username': 'test-user'}
            assert headers == {'X-RateLimit-Remaining': '4999'}
            mock_client.get.assert_called_once()

    async def test_make_request_post_method(self):
        """Test _make_request with POST method."""
        mock_response = Mock()

        mock_response.status_code = 201

        mock_response.json.return_value = {'created': True}
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            result, headers = await self.mixin._make_request(
                'https://api.bitbucket.org/2.0/repositories/workspace/repo/issues',
                params={'title': 'Test Issue'},
                method=RequestMethod.POST,
            )

            assert result == {'created': True}
            assert headers == {}
            mock_client.post.assert_called_once()

    async def test_make_request_with_token_refresh(self):
        """Test _make_request with token refresh on 401."""
        mixin = TestableBitBucketMixinBase(token=self.token, refresh=True)

        # First response returns 401, second response succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status = Mock()

        mock_response_200 = Mock()

        mock_response_200.status_code = 200

        mock_response_200.json.return_value = {'username': 'test-user'}
        mock_response_200.headers = {}
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
                    'https://api.bitbucket.org/2.0/user'
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
                await self.mixin._make_request(
                    'https://api.bitbucket.org/2.0/nonexistent'
                )

    async def test_make_request_http_error(self):
        """Test _make_request with general HTTP error."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError('Connection failed')
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(UnknownException):
                await self.mixin._make_request('https://api.bitbucket.org/2.0/user')

    async def test_fetch_paginated_data_single_page(self):
        """Test _fetch_paginated_data with single page."""
        response_data = {
            'values': [{'id': 1, 'name': 'item1'}, {'id': 2, 'name': 'item2'}]
        }

        with patch.object(
            self.mixin, '_make_request', return_value=(response_data, {})
        ):
            result = await self.mixin._fetch_paginated_data(
                'https://api.bitbucket.org/2.0/repositories',
                {'per_page': 10},
                max_items=100,
            )

            assert len(result) == 2
            assert result[0] == {'id': 1, 'name': 'item1'}
            assert result[1] == {'id': 2, 'name': 'item2'}

    async def test_fetch_paginated_data_multiple_pages(self):
        """Test _fetch_paginated_data with multiple pages."""
        page1_data = {
            'values': [{'id': 1, 'name': 'item1'}],
            'next': 'https://api.bitbucket.org/2.0/repositories?page=2',
        }
        page2_data = {'values': [{'id': 2, 'name': 'item2'}]}

        with patch.object(
            self.mixin,
            '_make_request',
            side_effect=[(page1_data, {}), (page2_data, {})],
        ):
            result = await self.mixin._fetch_paginated_data(
                'https://api.bitbucket.org/2.0/repositories',
                {'per_page': 1},
                max_items=100,
            )

            assert len(result) == 2
            assert result[0] == {'id': 1, 'name': 'item1'}
            assert result[1] == {'id': 2, 'name': 'item2'}

    async def test_fetch_paginated_data_max_items_limit(self):
        """Test _fetch_paginated_data respects max_items limit."""
        response_data = {
            'values': [
                {'id': 1, 'name': 'item1'},
                {'id': 2, 'name': 'item2'},
                {'id': 3, 'name': 'item3'},
            ]
        }

        with patch.object(
            self.mixin, '_make_request', return_value=(response_data, {})
        ):
            result = await self.mixin._fetch_paginated_data(
                'https://api.bitbucket.org/2.0/repositories',
                {'per_page': 10},
                max_items=2,
            )

            assert len(result) == 2
            assert result[0] == {'id': 1, 'name': 'item1'}
            assert result[1] == {'id': 2, 'name': 'item2'}

    async def test_get_user_success(self):
        """Test successful user retrieval."""
        user_data = {
            'account_id': 'abc123',
            'username': 'testuser',
            'display_name': 'Test User',
            'links': {
                'avatar': {'href': 'https://bitbucket.org/account/testuser/avatar/32/'}
            },
        }

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == 'abc123'
            assert user.login == 'testuser'
            assert user.name == 'Test User'
            assert (
                user.avatar_url == 'https://bitbucket.org/account/testuser/avatar/32/'
            )
            assert user.email is None  # Bitbucket doesn't return email

    async def test_get_user_with_missing_fields(self):
        """Test user retrieval with missing optional fields."""
        user_data = {'account_id': 'abc123', 'username': 'testuser'}

        with patch.object(self.mixin, '_make_request', return_value=(user_data, {})):
            user = await self.mixin.get_user()

            assert isinstance(user, User)
            assert user.id == 'abc123'
            assert user.login == 'testuser'
            assert user.name is None
            assert user.avatar_url == ''
            assert user.email is None

    def test_parse_repository_complete(self):
        """Test _parse_repository with complete repository data."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
            'is_private': False,
            'updated_on': '2023-01-01T00:00:00Z',
            'mainbranch': {'name': 'main'},
        }

        result = self.mixin._parse_repository(repo_data, 'link-header')

        assert isinstance(result, Repository)
        assert result.id == '{12345678-1234-1234-1234-123456789012}'
        assert result.full_name == 'test-workspace/test-repo'
        assert result.git_provider == ProviderType.BITBUCKET
        assert result.is_public is True
        assert result.stargazers_count is None  # Bitbucket doesn't have stars
        assert result.pushed_at == '2023-01-01T00:00:00Z'
        assert result.owner_type == OwnerType.ORGANIZATION
        assert result.link_header == 'link-header'
        assert result.main_branch == 'main'

    def test_parse_repository_minimal(self):
        """Test _parse_repository with minimal repository data."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {},
            'slug': '',
            'is_private': True,
        }

        result = self.mixin._parse_repository(repo_data)

        assert isinstance(result, Repository)
        assert result.id == '{12345678-1234-1234-1234-123456789012}'
        assert result.full_name == ''
        assert result.is_public is False
        assert result.main_branch is None

    async def test_get_repository_details_from_repo_name(self):
        """Test get_repository_details_from_repo_name."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
            'is_private': False,
            'mainbranch': {'name': 'main'},
        }

        with patch.object(self.mixin, '_make_request', return_value=(repo_data, {})):
            result = await self.mixin.get_repository_details_from_repo_name(
                'test-workspace/test-repo'
            )

            assert isinstance(result, Repository)
            assert result.full_name == 'test-workspace/test-repo'

    async def test_get_cursorrules_url(self):
        """Test _get_cursorrules_url method."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
            'mainbranch': {'name': 'main'},
        }

        with patch.object(
            self.mixin,
            'get_repository_details_from_repo_name',
            return_value=self.mixin._parse_repository(repo_data),
        ):
            url = await self.mixin._get_cursorrules_url('test-workspace/test-repo')

            expected_url = 'https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/src/main/.cursorrules'
            assert url == expected_url

    async def test_get_cursorrules_url_no_main_branch(self):
        """Test _get_cursorrules_url with no main branch."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
        }

        with patch.object(
            self.mixin,
            'get_repository_details_from_repo_name',
            return_value=self.mixin._parse_repository(repo_data),
        ):
            with pytest.raises(ResourceNotFoundError, match='Main branch not found'):
                await self.mixin._get_cursorrules_url('test-workspace/test-repo')

    async def test_get_microagents_directory_url(self):
        """Test _get_microagents_directory_url method."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
            'mainbranch': {'name': 'main'},
        }

        with patch.object(
            self.mixin,
            'get_repository_details_from_repo_name',
            return_value=self.mixin._parse_repository(repo_data),
        ):
            url = await self.mixin._get_microagents_directory_url(
                'test-workspace/test-repo', '.openhands/microagents'
            )

            expected_url = 'https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/src/main/.openhands/microagents'
            assert url == expected_url

    async def test_get_microagents_directory_url_no_main_branch(self):
        """Test _get_microagents_directory_url with no main branch."""
        repo_data = {
            'uuid': '{12345678-1234-1234-1234-123456789012}',
            'workspace': {'slug': 'test-workspace'},
            'slug': 'test-repo',
        }

        with patch.object(
            self.mixin,
            'get_repository_details_from_repo_name',
            return_value=self.mixin._parse_repository(repo_data),
        ):
            with pytest.raises(ResourceNotFoundError, match='Main branch not found'):
                await self.mixin._get_microagents_directory_url(
                    'test-workspace/test-repo', '.openhands/microagents'
                )

    def test_get_microagents_directory_params(self):
        """Test _get_microagents_directory_params method."""
        result = self.mixin._get_microagents_directory_params('.openhands/microagents')
        assert result is None

    def test_is_valid_microagent_file_valid(self):
        """Test _is_valid_microagent_file with valid microagent file."""
        item = {'type': 'commit_file', 'path': '.openhands/microagents/test.md'}

        assert self.mixin._is_valid_microagent_file(item) is True

    def test_is_valid_microagent_file_invalid_type(self):
        """Test _is_valid_microagent_file with invalid type."""
        item = {'type': 'commit_directory', 'path': '.openhands/microagents/test.md'}

        assert self.mixin._is_valid_microagent_file(item) is False

    def test_is_valid_microagent_file_invalid_extension(self):
        """Test _is_valid_microagent_file with invalid extension."""
        item = {'type': 'commit_file', 'path': '.openhands/microagents/test.txt'}

        assert self.mixin._is_valid_microagent_file(item) is False

    def test_is_valid_microagent_file_readme(self):
        """Test _is_valid_microagent_file with README file."""
        item = {'type': 'commit_file', 'path': '.openhands/microagents/README.md'}

        assert self.mixin._is_valid_microagent_file(item) is False

    def test_get_file_name_from_item(self):
        """Test _get_file_name_from_item method."""
        item = {'path': '.openhands/microagents/test-microagent.md'}

        result = self.mixin._get_file_name_from_item(item)
        assert result == 'test-microagent.md'

    def test_get_file_path_from_item(self):
        """Test _get_file_path_from_item method."""
        item = {'path': '.openhands/microagents/test-microagent.md'}

        result = self.mixin._get_file_path_from_item(item, '.openhands/microagents')
        assert result == '.openhands/microagents/test-microagent.md'

    async def test_execute_request_get(self):
        """Test execute_request with GET method."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_client.get.return_value = mock_response

        url = 'https://api.bitbucket.org/2.0/user'
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

        url = 'https://api.bitbucket.org/2.0/repositories/workspace/repo/issues'
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
        assert 'Invalid bitbucket token' in str(result)

    def test_handle_http_status_error_404(self):
        """Test handling of 404 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError(
            message='404 Not Found', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, ResourceNotFoundError)
        assert 'Resource not found on bitbucket API' in str(result)

    def test_handle_http_status_error_429(self):
        """Test handling of 429 HTTP status error."""
        mock_response = Mock()
        mock_response.status_code = 429

        error = httpx.HTTPStatusError(
            message='429 Too Many Requests', request=Mock(), response=mock_response
        )

        result = self.mixin.handle_http_status_error(error)
        assert isinstance(result, RateLimitError)
        assert 'bitbucket API rate limit exceeded' in str(result)

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
        assert self.mixin.provider == 'bitbucket'

    async def test_integration_full_request_cycle(self):
        """Test full request cycle integration."""
        # Mock a complete request/response cycle
        mock_response = Mock()

        mock_response.status_code = 200

        mock_response.json.return_value = {
            'username': 'testuser',
            'account_id': 'abc123',
        }
        mock_response.headers = {'X-RateLimit-Remaining': '4999'}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('httpx.AsyncClient', return_value=mock_client):
            # Test the full cycle: headers -> request -> response parsing
            headers = await self.mixin._get_headers()
            result, response_headers = await self.mixin._make_request(
                'https://api.bitbucket.org/2.0/user'
            )

            # Verify headers were constructed correctly
            assert 'Bearer test-token' in headers['Authorization']

            # Verify request was made with correct parameters
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'

            # Verify response was parsed correctly
            assert result == {'username': 'testuser', 'account_id': 'abc123'}
            assert response_headers == {'X-RateLimit-Remaining': '4999'}
