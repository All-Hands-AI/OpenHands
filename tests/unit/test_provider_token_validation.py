import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.utils import validate_provider_token
from openhands.server.routes.secrets import check_provider_tokens
from openhands.server.settings import POSTProviderModel


@pytest.mark.asyncio
async def test_validate_provider_token_with_bitbucket_token():
    """
    Test that validate_provider_token correctly identifies a Bitbucket token
    and doesn't try to validate it as GitHub or GitLab.
    """
    # Mock the service classes to avoid actual API calls
    with patch('openhands.integrations.utils.GitHubService') as mock_github_service, \
         patch('openhands.integrations.utils.GitLabService') as mock_gitlab_service, \
         patch('openhands.integrations.utils.BitbucketService') as mock_bitbucket_service:
        
        # Set up the mocks
        github_instance = AsyncMock()
        github_instance.verify_access.side_effect = Exception("Invalid GitHub token")
        mock_github_service.return_value = github_instance
        
        gitlab_instance = AsyncMock()
        gitlab_instance.get_user.side_effect = Exception("Invalid GitLab token")
        mock_gitlab_service.return_value = gitlab_instance
        
        bitbucket_instance = AsyncMock()
        bitbucket_instance.get_user.return_value = {"username": "test_user"}
        mock_bitbucket_service.return_value = bitbucket_instance
        
        # Test with a Bitbucket token
        token = SecretStr("username:app_password")
        result = await validate_provider_token(token)
        
        # Verify that all services were tried
        mock_github_service.assert_called_once()
        mock_gitlab_service.assert_called_once()
        mock_bitbucket_service.assert_called_once()
        
        # Verify that the token was identified as a Bitbucket token
        assert result == ProviderType.BITBUCKET


@pytest.mark.asyncio
async def test_check_provider_tokens_with_only_bitbucket():
    """
    Test that check_provider_tokens doesn't try to validate GitHub or GitLab tokens
    when only a Bitbucket token is provided.
    """
    # Create a mock validate_provider_token function
    mock_validate = AsyncMock()
    mock_validate.return_value = ProviderType.BITBUCKET
    
    # Create provider tokens with only Bitbucket
    provider_tokens = {
        ProviderType.BITBUCKET: ProviderToken(token=SecretStr("username:app_password"), host="bitbucket.org"),
        ProviderType.GITHUB: ProviderToken(token=SecretStr(""), host="github.com"),
        ProviderType.GITLAB: ProviderToken(token=SecretStr(""), host="gitlab.com"),
    }
    
    # Create the POST model
    post_model = POSTProviderModel(provider_tokens=provider_tokens)
    
    # Call check_provider_tokens with the patched validate_provider_token
    with patch('openhands.server.routes.secrets.validate_provider_token', mock_validate):
        result = await check_provider_tokens(post_model, None)
        
        # Verify that validate_provider_token was called only once (for Bitbucket)
        assert mock_validate.call_count == 1
        
        # Verify that the token passed to validate_provider_token was the Bitbucket token
        args, kwargs = mock_validate.call_args
        assert args[0].get_secret_value() == "username:app_password"
        
        # Verify that no error message was returned
        assert result == ""


@pytest.mark.asyncio
async def test_validate_provider_token_with_empty_tokens():
    """
    Test that validate_provider_token is not called for empty tokens.
    """
    # Create a mock for each service
    with patch('openhands.integrations.utils.GitHubService') as mock_github_service, \
         patch('openhands.integrations.utils.GitLabService') as mock_gitlab_service, \
         patch('openhands.integrations.utils.BitbucketService') as mock_bitbucket_service:
        
        # Test with an empty token
        token = SecretStr("")
        result = await validate_provider_token(token)
        
        # Verify that services were NOT tried (this is the fix)
        mock_github_service.assert_not_called()
        mock_gitlab_service.assert_not_called()
        mock_bitbucket_service.assert_not_called()
        
        # Result should be None for empty tokens
        assert result is None