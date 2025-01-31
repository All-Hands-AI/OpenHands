from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.core.config.sandbox_config import SandboxConfig
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
def test_client(mock_settings_store):
    # Mock the middleware that adds github_token
    class MockMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            settings = mock_settings_store.load.return_value
            token = settings.github_token if settings else None
            if scope['type'] == 'http':
                scope['state'] = {'github_token': token}
            await self.app(scope, receive, send)

    # Replace the middleware
    app.middleware_stack = None  # Clear existing middleware
    app.add_middleware(MockMiddleware)

    return TestClient(app)


@pytest.fixture
def mock_github_service():
    with patch('openhands.server.routes.settings.GitHubService') as mock:
        yield mock


@pytest.mark.asyncio
async def test_settings_api_runtime_factor(test_client, mock_settings_store):
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
    }

    # The test_client fixture already handles authentication

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the correct runtime factor
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.remote_runtime_resource_factor == 2

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    assert response.status_code == 200
    assert response.json()['remote_runtime_resource_factor'] == 2

    # Verify that the sandbox config gets updated when settings are loaded
    with patch('openhands.server.shared.config') as mock_config:
        mock_config.sandbox = SandboxConfig()
        response = test_client.get('/api/settings')
        assert response.status_code == 200

        # Verify that the sandbox config was updated with the new value
        mock_settings_store.store.assert_called()
        stored_settings = mock_settings_store.store.call_args[0][0]
        assert stored_settings.remote_runtime_resource_factor == 2

        assert isinstance(stored_settings.llm_api_key, SecretStr)
        assert stored_settings.llm_api_key.get_secret_value() == 'test-key'


@pytest.mark.asyncio
async def test_settings_llm_api_key(test_client, mock_settings_store):
    # Mock the settings store to return None initially (no existing settings)
    mock_settings_store.load.return_value = None

    # Test data with remote_runtime_resource_factor
    settings_data = {'llm_api_key': 'test-key'}

    # The test_client fixture already handles authentication

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the correct secret API key
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert isinstance(stored_settings.llm_api_key, SecretStr)
    assert stored_settings.llm_api_key.get_secret_value() == 'test-key'

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    assert response.status_code == 200

    # We should never expose the API key in the response
    assert 'test-key' not in response.json()


@pytest.mark.skip(
    reason='Mock middleware does not seem to properly set the github_token'
)
@pytest.mark.asyncio
async def test_settings_api_set_github_token(
    mock_github_service, test_client, mock_settings_store
):
    # Test data with github_token set
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': 'test-key',
        'llm_base_url': 'https://test.com',
        'github_token': 'test-token',
    }

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the github_token
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.github_token == 'test-token'

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    data = response.json()

    assert response.status_code == 200
    assert data.get('github_token') is None
    assert data['github_token_is_set'] is True


@pytest.mark.skip(
    reason='Mock middleware does not seem to properly set the github_token'
)
async def test_settings_unset_github_token(
    mock_github_service, test_client, mock_settings_store
):
    # Test data with unset_github_token set to True
    settings_data = {
        'language': 'en',
        'agent': 'test-agent',
        'max_iterations': 100,
        'security_analyzer': 'default',
        'confirmation_mode': True,
        'llm_model': 'test-model',
        'llm_api_key': 'test-key',
        'llm_base_url': 'https://test.com',
        'github_token': 'test-token',
    }

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = Settings(**settings_data)

    response = test_client.get('/api/settings')
    assert response.status_code == 200
    assert response.json()['github_token_is_set'] is True

    settings_data['unset_github_token'] = True

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the github_token unset
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.github_token is None
    mock_settings_store.load.return_value = Settings(**stored_settings.dict())

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    assert response.status_code == 200
    assert response.json()['github_token_is_set'] is False
