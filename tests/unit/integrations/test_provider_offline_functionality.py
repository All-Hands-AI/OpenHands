"""Tests for provider offline functionality and variable scope issues."""

from types import MappingProxyType
from unittest.mock import AsyncMock, patch

import pytest

from openhands.integrations.provider import ProviderHandler, ProviderToken, ProviderType
from openhands.integrations.service_types import AuthenticationError


class TestProviderOfflineFunctionality:
    """Test offline functionality and variable scope in ProviderHandler."""

    @pytest.fixture
    def provider_handler(self):
        """Create a ProviderHandler instance for testing."""
        tokens = MappingProxyType(
            {
                ProviderType.GITHUB: ProviderToken(token='test_token'),
                ProviderType.GITLAB: ProviderToken(token='gitlab_token'),
            }
        )
        return ProviderHandler(provider_tokens=tokens)

    @pytest.mark.asyncio
    async def test_get_authenticated_git_url_network_error_handling(
        self, provider_handler
    ):
        """Test that network errors are properly handled with fallback to inferred provider.

        After the fix, variables are properly initialized before the try block,
        ensuring they're always available regardless of which exception path is taken.
        """
        repo_name = 'test-owner/test-repo'

        # Mock verify_repo_provider to raise a non-AuthenticationError exception
        # This simulates a network error or other exception during offline operation
        with patch.object(provider_handler, 'verify_repo_provider') as mock_verify:
            # Simulate a network error (not AuthenticationError)
            mock_verify.side_effect = ConnectionError('Network unreachable')

            # After the fix, this should work correctly with proper variable initialization
            result = await provider_handler.get_authenticated_git_url(repo_name)

            # Should return a GitHub URL with token (inferred from repo name)
            assert result == 'https://test_token@github.com/test-owner/test-repo.git'

    @pytest.mark.asyncio
    async def test_get_authenticated_git_url_proper_variable_scope(
        self, provider_handler
    ):
        """Test that verifies the variables are properly scoped after the fix.

        This test ensures that after fixing the code structure, the variables
        'provider' and 'repo_name' are properly initialized and available
        regardless of which exception path is taken.
        """
        repo_name = 'test-owner/test-repo'

        # Test with network error - should use inferred provider and original repo_name
        with patch.object(provider_handler, 'verify_repo_provider') as mock_verify:
            mock_verify.side_effect = ConnectionError('Network unreachable')

            result = await provider_handler.get_authenticated_git_url(repo_name)

            # Should return authenticated URL with inferred GitHub provider
            assert result == 'https://test_token@github.com/test-owner/test-repo.git'

        # Test with successful verification - should use verified provider and repo_name
        mock_repository = AsyncMock()
        mock_repository.git_provider = ProviderType.GITLAB
        mock_repository.full_name = 'verified-owner/verified-repo'

        with patch.object(provider_handler, 'verify_repo_provider') as mock_verify:
            mock_verify.return_value = mock_repository

            result = await provider_handler.get_authenticated_git_url(repo_name)

            # Should return authenticated GitLab URL with verified details
            assert (
                result
                == 'https://oauth2:gitlab_token@gitlab.com/verified-owner/verified-repo.git'
            )

    @pytest.mark.asyncio
    async def test_get_authenticated_git_url_auth_error_handling(
        self, provider_handler
    ):
        """Test that AuthenticationError is properly handled and re-raised."""
        repo_name = 'test-owner/test-repo'

        # Mock verify_repo_provider to raise AuthenticationError
        with patch.object(provider_handler, 'verify_repo_provider') as mock_verify:
            mock_verify.side_effect = AuthenticationError('Invalid token')

            # AuthenticationError should be re-raised as a generic Exception
            with pytest.raises(Exception) as exc_info:
                await provider_handler.get_authenticated_git_url(repo_name)

            assert 'Git provider authentication issue when getting remote URL' in str(
                exc_info.value
            )

    @pytest.mark.asyncio
    async def test_get_authenticated_git_url_successful_case(self, provider_handler):
        """Test the successful case where repository verification works."""
        repo_name = 'test-owner/test-repo'

        # Mock a successful repository verification
        mock_repository = AsyncMock()
        mock_repository.git_provider = ProviderType.GITHUB
        mock_repository.full_name = 'test-owner/test-repo'

        with patch.object(provider_handler, 'verify_repo_provider') as mock_verify:
            mock_verify.return_value = mock_repository

            result = await provider_handler.get_authenticated_git_url(repo_name)

            # Should return an authenticated GitHub URL
            assert result == 'https://test_token@github.com/test-owner/test-repo.git'
