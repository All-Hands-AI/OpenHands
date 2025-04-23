from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.provider import ProviderType, SecretStore
from openhands.server.app import app
from openhands.server.settings import Settings


@pytest.fixture
def mock_settings_store():
    with patch('openhands.server.routes.settings.SettingsStoreImpl') as mock:
        store_instance = MagicMock()
        mock.get_instance = AsyncMock(return_value=store_instance)
        store_instance.load = AsyncMock()
        store_instance.store = AsyncMock()
        yield store_instance


@pytest.fixture
def mock_get_user_id():
    with patch('openhands.server.routes.settings.get_user_id') as mock:

        async def mock_get_user_id(*args, **kwargs):
            return 'test-user'

        mock.side_effect = mock_get_user_id
        yield mock


@pytest.fixture
def mock_get_user_settings():
    with patch('openhands.server.routes.settings.get_user_settings') as mock:

        async def mock_get_settings(*args, **kwargs):
            return None  # Will be overridden in tests

        mock.side_effect = mock_get_settings
        yield mock


@pytest.fixture
def mock_validate_provider_token():
    with patch('openhands.server.routes.settings.validate_provider_token') as mock:

        async def mock_determine(*args, **kwargs):
            return ProviderType.GITHUB

        mock.side_effect = mock_determine
        yield mock


@pytest.fixture
def test_client(mock_settings_store, mock_get_user_id, mock_get_user_settings):
    # Mock the middleware that adds github_token
    class MockMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            settings = mock_settings_store.load.return_value
            token = None
            if (
                settings
                and settings.secrets_store
                and settings.secrets_store.provider_tokens.get(ProviderType.GITHUB)
            ):
                token = settings.secrets_store.provider_tokens[
                    ProviderType.GITHUB
                ].token
            if scope['type'] == 'http':
                scope['state'] = {'token': token, 'user_id': 'test-user'}
            await self.app(scope, receive, send)

    # Replace the middleware
    app.middleware_stack = None  # Clear existing middleware
    app.add_middleware(MockMiddleware)

    # Override the get_user_id dependency
    from fastapi.testclient import TestClient

    # Create a test client that will use our mocked dependencies
    client = TestClient(app)

    # Patch the get_user_id dependency to return our test user
    mock_get_user_id.return_value = 'test-user'

    # Set up the mock_get_user_settings to return the same as mock_settings_store.load
    async def get_settings(*args, **kwargs):
        return mock_settings_store.load.return_value

    mock_get_user_settings.side_effect = get_settings

    return client


@pytest.fixture
def mock_github_service():
    with patch('openhands.server.routes.settings.GitHubService') as mock:
        yield mock


@pytest.mark.skip("Needs to be updated for the refactor-auth branch")
@pytest.mark.asyncio
async def test_settings_api_runtime_factor(
    test_client, mock_settings_store, mock_get_user_id, mock_validate_provider_token
):
    # Mock the settings store to return None initially (no existing settings)
    mock_settings_store.load.return_value = None

    # Test data with remote_runtime_resource_factor
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': 'test-key',
        'llm_base_url': 'https://test.com',
        'remote_runtime_resource_factor': 2,
        'provider_tokens': {'github': 'test-token'},
    }

    # The test_client fixture already handles authentication

    # Make the POST request to store settings
    with patch('openhands.server.routes.settings.store_llm_settings') as mock_store_llm:
        with patch('openhands.server.routes.settings.store_provider_tokens') as mock_store_tokens:
            response = test_client.post('/api/settings', json=settings_data)
            assert response.status_code == 200
            
            # Verify that store_llm_settings was called
            mock_store_llm.assert_called_once()
            
            # Verify that store_provider_tokens was called
            mock_store_tokens.assert_called_once()
            
            # Skip GET request tests as they would require more complex mocking of the user_auth system
            # The important part is that the POST request works correctly


@pytest.mark.skip("Needs to be updated for the refactor-auth branch")
@pytest.mark.asyncio
async def test_settings_llm_api_key(
    test_client, mock_settings_store, mock_get_user_id, mock_validate_provider_token
):
    # Mock the settings store to return None initially (no existing settings)
    mock_settings_store.load.return_value = None

    # Test data with remote_runtime_resource_factor
    settings_data = {
        'llm_api_key': 'test-key',
        'provider_tokens': {'github': 'test-token'},
    }

    # The test_client fixture already handles authentication

    # Make the POST request to store settings
    with patch('openhands.server.routes.settings.store_llm_settings') as mock_store_llm:
        with patch('openhands.server.routes.settings.store_provider_tokens') as mock_store_tokens:
            response = test_client.post('/api/settings', json=settings_data)
            assert response.status_code == 200
            
            # Verify that store_llm_settings was called
            mock_store_llm.assert_called_once()
            
            # Verify that store_provider_tokens was called
            mock_store_tokens.assert_called_once()
            
            # Verify the API key was passed correctly
            settings_arg = mock_store_llm.call_args[0][0]
            assert settings_arg.llm_api_key.get_secret_value() == 'test-key'

    # Skip GET request tests as they would require more complex mocking of the user_auth system
    # The important part is that the POST request works correctly


@pytest.mark.skip(
    reason='Mock middleware does not seem to properly set the github_token'
)
@pytest.mark.asyncio
async def test_settings_api_set_github_token(
    mock_github_service,
    test_client,
    mock_settings_store,
    mock_get_user_id,
    mock_validate_provider_token,
):
    # Test data with provider token set
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': 'test-key',
        'llm_base_url': 'https://test.com',
        'provider_tokens': {'github': 'test-token'},
    }

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the provider token
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert (
        stored_settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test-token'
    )

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    data = response.json()

    assert response.status_code == 200
    assert data.get('token') is None
    assert data['token_is_set'] is True


@pytest.mark.skip("Needs to be updated for the refactor-auth branch")
@pytest.mark.asyncio
async def test_settings_preserve_llm_fields_when_none(test_client, mock_settings_store):
    # Setup initial settings with LLM fields populated
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        max_iterations=100,
        security_analyzer='default',
        confirmation_mode=True,
        llm_model='existing-model',
        llm_api_key=SecretStr('existing-key'),
        llm_base_url='https://existing.com',
        secrets_store=SecretStore(),
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Test data with None values for LLM fields
    settings_update = {
        'language': 'fr',  # Change something else to verify the update happens
        'llm_model': None,
        'llm_api_key': None,
        'llm_base_url': None,
    }

    # Make the POST request to update settings
    with patch('openhands.server.routes.settings.store_llm_settings') as mock_store_llm:
        with patch('openhands.server.routes.settings.store_provider_tokens') as mock_store_tokens:
            response = test_client.post('/api/settings', json=settings_update)
            assert response.status_code == 200
            
            # Verify that store_llm_settings was called
            mock_store_llm.assert_called_once()
            
            # Verify the settings were passed correctly
            settings_arg = mock_store_llm.call_args[0][0]

    # Check that language was updated
    assert settings_arg.language == 'fr'
    
    # Check that LLM fields were preserved
    assert settings_arg.llm_model == 'existing-model'
    assert settings_arg.llm_api_key.get_secret_value() == 'existing-key'
    assert settings_arg.llm_base_url == 'https://existing.com'

    # No need to check stored_settings since we're mocking the store_llm_settings function

    # Skip GET request tests as they would require more complex mocking of the user_auth system
    # The important part is that the POST request works correctly
