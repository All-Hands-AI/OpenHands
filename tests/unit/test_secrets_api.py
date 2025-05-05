"""Tests for the custom secrets API endpoints."""
# flake8: noqa: E501

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.server.routes.secrets import app as secrets_app
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.file_secrets_store import FileSecretsStore


@pytest.fixture
def test_client():
    """Create a test client for the settings API."""
    app = FastAPI()
    app.include_router(secrets_app)
    return TestClient(app)


@pytest.fixture
def temp_dir(tmp_path_factory: pytest.TempPathFactory) -> str:
    return str(tmp_path_factory.mktemp('secrets_store'))


@pytest.fixture
def file_secrets_store(temp_dir):
    file_store = get_file_store('local', temp_dir)
    store = FileSecretsStore(file_store)
    with patch(
        'openhands.storage.secrets.file_secrets_store.FileSecretsStore.get_instance',
        AsyncMock(return_value=store),
    ):
        yield store


@pytest.mark.asyncio
async def test_load_custom_secrets_names(test_client, file_secrets_store):
    """Test loading custom secrets names."""

    # Create initial settings with custom secrets
    custom_secrets = {
        'API_KEY': SecretStr('api-key-value'),
        'DB_PASSWORD': SecretStr('db-password-value'),
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the GET request
    response = test_client.get('/api/secrets')
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'custom_secrets' in data
    assert sorted(data['custom_secrets']) == ['API_KEY', 'DB_PASSWORD']

    # Verify that the original settings were not modified
    stored_settings = await file_secrets_store.load()
    assert (
        stored_settings.custom_secrets['API_KEY'].get_secret_value() == 'api-key-value'
    )
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].get_secret_value()
        == 'db-password-value'
    )
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_load_custom_secrets_names_empty(test_client, file_secrets_store):
    """Test loading custom secrets names when there are no custom secrets."""
    # Create initial settings with no custom secrets
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(provider_tokens=provider_tokens)

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the GET request
    response = test_client.get('/api/secrets')
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'custom_secrets' in data
    assert data['custom_secrets'] == []


@pytest.mark.asyncio
async def test_add_custom_secret(test_client, file_secrets_store):
    """Test adding a new custom secret."""

    # Create initial settings with provider tokens but no custom secrets
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(provider_tokens=provider_tokens)

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the POST request to add a custom secret
    add_secret_data = {'custom_secrets': {'API_KEY': 'api-key-value'}}
    response = test_client.post('/api/secrets', json=add_secret_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the new secret
    stored_settings = await file_secrets_store.load()

    # Check that the secret was added
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].get_secret_value() == 'api-key-value'
    )


@pytest.mark.asyncio
async def test_update_existing_custom_secret(test_client, file_secrets_store):
    """Test updating an existing custom secret."""

    # Create initial settings with a custom secret
    custom_secrets = {'API_KEY': SecretStr('old-api-key')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the POST request to update the custom secret
    update_secret_data = {'custom_secrets': {'API_KEY': 'new-api-key'}}
    response = test_client.put('/api/secrets/API_KEY', json=update_secret_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the updated secret
    stored_settings = await file_secrets_store.load()

    # Check that the secret was updated
    assert 'API_KEY' in stored_settings.custom_secrets
    assert stored_settings.custom_secrets['API_KEY'].get_secret_value() == 'new-api-key'

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_add_multiple_custom_secrets(test_client, file_secrets_store):
    """Test adding multiple custom secrets at once."""

    # Create initial settings with one custom secret
    custom_secrets = {'EXISTING_SECRET': SecretStr('existing-value')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

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
    stored_settings = await file_secrets_store.load()

    # Check that the new secrets were added
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].get_secret_value() == 'api-key-value'
    )
    assert 'DB_PASSWORD' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].get_secret_value()
        == 'db-password-value'
    )

    # Check that existing secrets were preserved
    assert 'EXISTING_SECRET' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['EXISTING_SECRET'].get_secret_value()
        == 'existing-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_delete_custom_secret(test_client, file_secrets_store):
    """Test deleting a custom secret."""

    # Create initial settings with multiple custom secrets
    custom_secrets = {
        'API_KEY': SecretStr('api-key-value'),
        'DB_PASSWORD': SecretStr('db-password-value'),
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the DELETE request to delete a custom secret
    response = test_client.delete('/api/secrets/API_KEY')
    assert response.status_code == 200

    # Verify that the settings were stored without the deleted secret
    stored_settings = await file_secrets_store.load()

    # Check that the specified secret was deleted
    assert 'API_KEY' not in stored_settings.custom_secrets

    # Check that other secrets were preserved
    assert 'DB_PASSWORD' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].get_secret_value()
        == 'db-password-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_delete_nonexistent_custom_secret(test_client, file_secrets_store):
    """Test deleting a custom secret that doesn't exist."""

    # Create initial settings with a custom secret
    custom_secrets = {'API_KEY': SecretStr('api-key-value')}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the DELETE request to delete a nonexistent custom secret
    response = test_client.delete('/api/secrets/NONEXISTENT_KEY')
    assert response.status_code == 404

    # Verify that the settings were stored without changes to existing secrets
    stored_settings = await file_secrets_store.load()

    # Check that the existing secret was preserved
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].get_secret_value() == 'api-key-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens
