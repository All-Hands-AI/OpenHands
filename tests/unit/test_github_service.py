import pytest
from pydantic import SecretStr
from openhands.services.github.github_service import GitHubService
from openhands.services.github.github_types import GhAuthenticationError

@pytest.mark.asyncio
async def test_github_service_token_handling():
    # Test initialization with SecretStr token
    token = SecretStr('test-token')
    service = GitHubService(user_id=None, token=token)
    assert service.token == token
    assert service.token.get_secret_value() == 'test-token'

    # Test headers contain the token correctly
    headers = await service._get_github_headers()
    assert headers['Authorization'] == 'Bearer test-token'
    assert headers['Accept'] == 'application/vnd.github.v3+json'

    # Test initialization without token
    service = GitHubService(user_id='test-user')
    assert service.token == SecretStr('')

@pytest.mark.asyncio
async def test_github_service_token_refresh():
    # Test that token refresh is only attempted when refresh=True
    service = GitHubService(user_id=None, token=SecretStr('test-token'))
    assert not service.refresh
    
    # Test token expiry detection
    assert service._has_token_expired(401)
    assert not service._has_token_expired(200)
    assert not service._has_token_expired(404)

    # Test get_latest_token returns the current token by default
    latest_token = await service.get_latest_token()
    assert isinstance(latest_token, SecretStr)
    assert latest_token.get_secret_value() == 'test-token'

@pytest.mark.asyncio
async def test_github_service_fetch_data(mocker):
    # Mock httpx.AsyncClient for testing API calls
    mock_client = mocker.AsyncMock()
    mock_response = mocker.AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'login': 'test-user'}
    mock_client.get.return_value = mock_response
    
    mocker.patch('httpx.AsyncClient', return_value=mock_client)

    service = GitHubService(user_id=None, token=SecretStr('test-token'))
    data = await service._fetch_data('https://api.github.com/user')
    
    # Verify the request was made with correct headers
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    headers = call_args[1]['headers']
    assert headers['Authorization'] == 'Bearer test-token'

    # Test error handling
    mock_response.status_code = 401
    mock_response.json.return_value = {'message': 'Bad credentials'}
    
    with pytest.raises(GhAuthenticationError):
        await service._fetch_data('https://api.github.com/user')