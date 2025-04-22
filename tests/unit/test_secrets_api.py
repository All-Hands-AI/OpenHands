"""Tests for the custom secrets API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from openhands.server.routes.settings import app as settings_app
from openhands.server.settings import Settings


@pytest.fixture
def test_client():
    """Create a test client for the settings API."""
    app = FastAPI()
    app.include_router(settings_app)
    return TestClient(app)


@pytest.fixture
def mock_settings_store():
    with patch('openhands.server.routes.settings.SettingsStoreImpl') as mock:
        store_instance = MagicMock()
        mock.get_instance = AsyncMock(return_value=store_instance)
        store_instance.load = AsyncMock()
        store_instance.store = AsyncMock()
        yield store_instance


@pytest.fixture
def mock_convert_to_settings():
    with patch('openhands.server.routes.settings.convert_to_settings') as mock:
        # Make the mock function pass through the input settings
        mock.side_effect = lambda settings: settings
        yield mock


@pytest.fixture
def mock_get_user_id():
    with patch('openhands.server.routes.settings.get_user_id') as mock:
        mock.return_value = 'test-user'
        yield mock


@pytest.mark.asyncio
async def test_load_custom_secrets_names(test_client, mock_settings_store):
    """Test loading custom secrets names."""
    # Create initial settings with custom secrets
    custom_secrets = {
        'API_KEY': SecretStr('api-key-value'),
        'DB_PASSWORD': SecretStr('db-password-value'),
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the GET request
    response = test_client.get('/api/secrets')
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'custom_secrets' in data
    assert sorted(data['custom_secrets']) == ['API_KEY', 'DB_PASSWORD']


@pytest.mark.asyncio
async def test_load_custom_secrets_names_empty(test_client, mock_settings_store):
    """Test loading custom secrets names when there are no custom secrets."""
    # Create initial settings with no custom secrets
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(provider_tokens=provider_tokens)
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the GET request
    response = test_client.get('/api/secrets')
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'custom_secrets' in data
    assert data['custom_secrets'] == []


@pytest.mark.asyncio
async def test_add_custom_secret(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test adding a new custom secret."""
    # Create initial settings with provider tokens but no custom secrets
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(provider_tokens=provider_tokens)
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the POST request to add a custom secret
    add_secret_data = {'custom_secrets': {'API_KEY': 'api-key-value'}}
    response = test_client.post('/api/secrets', json=add_secret_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the new secret
    stored_settings = mock_settings_store.store.call_args[0][0]

    # Check that the secret was added
    assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['API_KEY'].get_secret_value()
        == 'api-key-value'
    )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'


@pytest.mark.asyncio
async def test_update_existing_custom_secret(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test updating an existing custom secret."""
    # Create initial settings with a custom secret
    custom_secrets = {'API_KEY': SecretStr('old-api-key')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the POST request to update the custom secret
    update_secret_data = {'custom_secrets': {'API_KEY': 'new-api-key'}}
    response = test_client.post('/api/secrets', json=update_secret_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the updated secret
    stored_settings: Settings = mock_settings_store.store.call_args[0][0]

    # Check that the secret was updated
    assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['API_KEY'].get_secret_value()
        == 'new-api-key'
    )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
    assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_add_multiple_custom_secrets(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test adding multiple custom secrets at once."""
    # Create initial settings with one custom secret
    custom_secrets = {'EXISTING_SECRET': SecretStr('existing-value')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the POST request to add multiple custom secrets
    add_secrets_data = {
        'custom_secrets': {
            'API_KEY': 'api-key-value',
            'DB_PASSWORD': 'db-password-value',
        }
    }
    response = test_client.post('/api/secrets', json=add_secrets_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the new secrets
    stored_settings = mock_settings_store.store.call_args[0][0]

    # Check that the new secrets were added
    assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['API_KEY'].get_secret_value()
        == 'api-key-value'
    )
    assert 'DB_PASSWORD' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['DB_PASSWORD'].get_secret_value()
        == 'db-password-value'
    )

    # Check that existing secrets were preserved
    assert 'EXISTING_SECRET' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets[
            'EXISTING_SECRET'
        ].get_secret_value()
        == 'existing-value'
    )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'


@pytest.mark.asyncio
async def test_delete_custom_secret(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test deleting a custom secret."""
    # Create initial settings with multiple custom secrets
    custom_secrets = {
        'API_KEY': SecretStr('api-key-value'),
        'DB_PASSWORD': SecretStr('db-password-value'),
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the DELETE request to delete a custom secret
    response = test_client.delete('/api/secrets/API_KEY')
    assert response.status_code == 200

    # Verify that the settings were stored without the deleted secret
    stored_settings = mock_settings_store.store.call_args[0][0]

    # Check that the specified secret was deleted
    assert 'API_KEY' not in stored_settings.secrets_store.custom_secrets

    # Check that other secrets were preserved
    assert 'DB_PASSWORD' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['DB_PASSWORD'].get_secret_value()
        == 'db-password-value'
    )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'


@pytest.mark.asyncio
async def test_delete_nonexistent_custom_secret(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test deleting a custom secret that doesn't exist."""
    # Create initial settings with a custom secret
    custom_secrets = {'API_KEY': SecretStr('api-key-value')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        llm_api_key=SecretStr('test-llm-key'),
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # Make the DELETE request to delete a nonexistent custom secret
    response = test_client.delete('/api/secrets/NONEXISTENT_KEY')
    assert response.status_code == 200

    # Verify that the settings were stored without changes to existing secrets
    stored_settings = mock_settings_store.store.call_args[0][0]

    # Check that the existing secret was preserved
    assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
    assert (
        stored_settings.secrets_store.custom_secrets['API_KEY'].get_secret_value()
        == 'api-key-value'
    )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'


@pytest.mark.asyncio
async def test_custom_secrets_operations_preserve_settings(
    test_client, mock_settings_store, mock_convert_to_settings
):
    """Test that operations on custom secrets preserve all other settings."""
    # Create initial settings with comprehensive data
    custom_secrets = {'INITIAL_SECRET': SecretStr('initial-value')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token')),
        ProviderType.GITLAB: ProviderToken(token=SecretStr('gitlab-token')),
    }
    secret_store = SecretStore(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )
    initial_settings = Settings(
        language='en',
        agent='test-agent',
        max_iterations=100,
        security_analyzer='default',
        confirmation_mode=True,
        llm_model='test-model',
        llm_api_key=SecretStr('test-llm-key'),
        llm_base_url='https://test.com',
        remote_runtime_resource_factor=2,
        enable_default_condenser=True,
        enable_sound_notifications=False,
        user_consents_to_analytics=True,
        secrets_store=secret_store,
    )

    # Mock the settings store to return our initial settings
    mock_settings_store.load.return_value = initial_settings

    # 1. Test adding a new custom secret
    add_secret_data = {'custom_secrets': {'NEW_SECRET': 'new-value'}}
    response = test_client.post('/api/secrets', json=add_secret_data)
    assert response.status_code == 200

    # Verify all settings are preserved
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.max_iterations == 100
    assert stored_settings.security_analyzer == 'default'
    assert stored_settings.confirmation_mode is True
    assert stored_settings.llm_model == 'test-model'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
    assert stored_settings.llm_base_url == 'https://test.com'
    assert stored_settings.remote_runtime_resource_factor == 2
    assert stored_settings.enable_default_condenser is True
    assert stored_settings.enable_sound_notifications is False
    assert stored_settings.user_consents_to_analytics is True
    assert len(stored_settings.secrets_store.provider_tokens) == 2

    # 2. Test updating an existing custom secret
    update_secret_data = {'custom_secrets': {'INITIAL_SECRET': 'updated-value'}}
    response = test_client.post('/api/secrets', json=update_secret_data)
    assert response.status_code == 200

    # Verify all settings are still preserved
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.max_iterations == 100
    assert stored_settings.security_analyzer == 'default'
    assert stored_settings.confirmation_mode is True
    assert stored_settings.llm_model == 'test-model'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
    assert stored_settings.llm_base_url == 'https://test.com'
    assert stored_settings.remote_runtime_resource_factor == 2
    assert stored_settings.enable_default_condenser is True
    assert stored_settings.enable_sound_notifications is False
    assert stored_settings.user_consents_to_analytics is True
    assert len(stored_settings.secrets_store.provider_tokens) == 2

    # 3. Test deleting a custom secret
    response = test_client.delete('/api/secrets/NEW_SECRET')
    assert response.status_code == 200

    # Verify all settings are still preserved
    stored_settings = mock_settings_store.store.call_args[0][0]
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.max_iterations == 100
    assert stored_settings.security_analyzer == 'default'
    assert stored_settings.confirmation_mode is True
    assert stored_settings.llm_model == 'test-model'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
    assert stored_settings.llm_base_url == 'https://test.com'
    assert stored_settings.remote_runtime_resource_factor == 2
    assert stored_settings.enable_default_condenser is True
    assert stored_settings.enable_sound_notifications is False
    assert stored_settings.user_consents_to_analytics is True
    assert len(stored_settings.secrets_store.provider_tokens) == 2
