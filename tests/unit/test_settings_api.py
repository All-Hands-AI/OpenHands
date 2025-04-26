from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.server.app import app
from openhands.server.user_auth.user_auth import UserAuth
from openhands.storage.settings.settings_store import SettingsStore


class MockUserAuth(UserAuth):
    """Mock implementation of UserAuth for testing"""

    def __init__(self):
        self._settings = None
        self._settings_store = MagicMock()
        self._settings_store.load = AsyncMock(return_value=None)
        self._settings_store.store = AsyncMock()

    async def get_user_id(self) -> str | None:
        return 'test-user'

    async def get_access_token(self) -> SecretStr | None:
        return SecretStr('test-token')

    async def get_provider_tokens(self) -> dict[ProviderType, ProviderToken] | None:  # noqa: E501
        return None

    async def get_user_settings_store(self) -> SettingsStore | None:
        return self._settings_store

    @classmethod
    async def get_instance(cls, request: Request) -> UserAuth:
        return MockUserAuth()


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
        mock.return_value = 'test-user'
        yield mock


@pytest.fixture
def mock_validate_provider_token():
    with patch('openhands.server.routes.settings.validate_provider_token') as mock:

        async def mock_determine(*args, **kwargs):
            # Default to GitHub, but can be overridden in tests
            token_value = args[0].get_secret_value() if args else ''
            if 'azure' in token_value.lower():
                return ProviderType.AZUREDEVOPS
            elif 'gitlab' in token_value.lower():
                return ProviderType.GITLAB
            else:
                return ProviderType.GITHUB

        mock.side_effect = mock_determine
        yield mock


@pytest.fixture
def test_client(mock_settings_store):
    # Mock the middleware that adds github_token
    class MockMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            settings = mock_settings_store.load.return_value
            token = None
            if settings and settings.secrets_store.provider_tokens.get(
                ProviderType.GITHUB
            ):
                token = settings.secrets_store.provider_tokens[
                    ProviderType.GITHUB
                ].token
            if scope['type'] == 'http':
                scope['state'] = {'token': token}
            await self.app(scope, receive, send)

    # Replace the middleware
    app.middleware_stack = None  # Clear existing middleware
    app.add_middleware(MockMiddleware)

    return TestClient(app)


@pytest.fixture
def mock_github_service():
    with patch('openhands.server.routes.settings.GitHubService') as mock:
        yield mock
def test_client():
    # Create a test client
    with patch(
        'openhands.server.user_auth.user_auth.UserAuth.get_instance',
        return_value=MockUserAuth(),
    ):
        with patch(
            'openhands.server.routes.settings.validate_provider_token',
            return_value=ProviderType.GITHUB,
        ):
            client = TestClient(app)
            yield client


@pytest.mark.asyncio
async def test_settings_api_endpoints(test_client):
    """Test that the settings API endpoints work with the new auth system"""

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

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)

    # We're not checking the exact response, just that it doesn't error
    assert response.status_code == 200

    # Test the GET settings endpoint
    response = test_client.get('/api/settings')
    assert response.status_code == 200

    # Test updating with partial settings
    partial_settings = {
        'language': 'fr',
        'llm_model': None,  # Should preserve existing value
        'llm_api_key': None,  # Should preserve existing value
    }

    response = test_client.post('/api/settings', json=partial_settings)
    assert response.status_code == 200

    # Test the unset-settings-tokens endpoint
    response = test_client.post('/api/unset-settings-tokens')
    assert response.status_code == 200

    # We should never expose the API key in the response
    assert 'test-key' not in response.json()


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
    response = test_client.post('/api/settings', json=settings_update)
    assert response.status_code == 200

    # Verify that the settings were stored with preserved LLM values
    stored_settings = mock_settings_store.store.call_args[0][0]

    # Check that language was updated
    assert stored_settings.language == 'fr'

    # Check that LLM fields were preserved and not cleared
    assert stored_settings.llm_model == 'existing-model'
    assert isinstance(stored_settings.llm_api_key, SecretStr)
    assert stored_settings.llm_api_key.get_secret_value() == 'existing-key'
    assert stored_settings.llm_base_url == 'https://existing.com'

    # Update the mock to return our new settings for the GET request
    mock_settings_store.load.return_value = stored_settings

    # Make a GET request to verify the updated settings
    response = test_client.get('/api/settings')
    assert response.status_code == 200
    data = response.json()

    # Verify fields in the response
    assert data['language'] == 'fr'
    assert data['llm_model'] == 'existing-model'
    assert data['llm_base_url'] == 'https://existing.com'
    # We expect the API key not to be included in the response
    assert 'test-key' not in str(response.content)


@pytest.mark.asyncio
async def test_settings_azuredevops_token(
    test_client, mock_settings_store, mock_get_user_id, mock_validate_provider_token
):
    # Mock the settings store to return None initially (no existing settings)
    mock_settings_store.load.return_value = None

    # Test data with Azure DevOps token
    settings_data = {
        'provider_tokens': {'azuredevops': 'azure-test-token'},
    }

    # Make the POST request to store settings
    response = test_client.post('/api/settings', json=settings_data)
    assert response.status_code == 200

    # Verify the settings were stored with the correct provider token
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.secrets_store is not None

    # Check that the token was stored with the correct provider type
    provider_tokens = stored_settings.secrets_store.provider_tokens
    assert ProviderType.AZUREDEVOPS in provider_tokens
    assert isinstance(provider_tokens[ProviderType.AZUREDEVOPS].token, SecretStr)
    assert (
        provider_tokens[ProviderType.AZUREDEVOPS].token.get_secret_value()
        == 'azure-test-token'
    )

    # Mock settings store to return our settings for the GET request
    mock_settings_store.load.return_value = stored_settings

    # Make a GET request to retrieve settings
    response = test_client.get('/api/settings')
    data = response.json()

    assert response.status_code == 200
    assert data.get('token') is None
    assert data['token_is_set'] is True
    assert 'provider_tokens_set' in data
    assert data['provider_tokens_set'].get('azuredevops') is True
    # We'll skip the secrets endpoints for now as they require more complex mocking  # noqa: E501
    # and they're not directly related to the authentication refactoring
