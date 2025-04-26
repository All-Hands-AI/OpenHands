"""Tests for the custom secrets API endpoints."""
# flake8: noqa: E501

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import (
    CustomSecret,
    ProviderToken,
    ProviderType,
    SecretStore,
)
from openhands.server.routes.settings import app as settings_app
from openhands.server.settings import Settings
from openhands.storage.memory import InMemoryFileStore
from openhands.storage.settings.file_settings_store import FileSettingsStore


@pytest.fixture
def test_client():
    """Create a test client for the settings API."""
    app = FastAPI()
    app.include_router(settings_app)
    return TestClient(app)


@contextmanager
def patch_file_settings_store():
    store = FileSettingsStore(InMemoryFileStore())

    # Create a mock for the settings store
    with patch(
        'openhands.storage.settings.file_settings_store.FileSettingsStore.get_instance',
        AsyncMock(return_value=store),
    ):
        # Create a mock for the get_user_settings_store dependency
        with patch(
            'openhands.server.user_auth.get_user_settings_store',
            new=AsyncMock(return_value=store),
        ):
            # Create a mock for the get_user_settings dependency
            with patch(
                'openhands.server.user_auth.get_user_settings',
                new=AsyncMock(side_effect=lambda request=None: store.load()),
            ):
                yield store


@pytest.mark.asyncio
async def test_load_custom_secrets_names(test_client):
    """Test loading custom secrets names."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with custom secrets
        custom_secrets = {
            'API_KEY': CustomSecret(
                secret=SecretStr('api-key-value'), description='api key'
            ),
            'DB_PASSWORD': CustomSecret(
                secret=SecretStr('db-password-value'),
                description='password for postgres db',
            ),
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the GET request
        response = test_client.get('/api/secrets')
        assert response.status_code == 200

        # Check the response
        data = response.json()
        assert 'custom_secrets' in data
        assert sorted(data['custom_secrets']) == ['API_KEY', 'DB_PASSWORD']

        # Verify that the original settings were not modified
        stored_settings = await file_settings_store.load()
        assert (
            stored_settings.secrets_store.custom_secrets[
                'API_KEY'
            ].secret.get_secret_value()
            == 'api-key-value'
        )
        assert (
            stored_settings.secrets_store.custom_secrets[
                'DB_PASSWORD'
            ].secret.get_secret_value()
            == 'db-password-value'
        )
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_load_custom_secrets_names_empty(test_client):
    """Test loading custom secrets names when there are no custom secrets."""
    with patch_file_settings_store() as file_settings_store:
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the GET request
        response = test_client.get('/api/secrets')
        assert response.status_code == 200

        # Check the response
        data = response.json()
        assert 'custom_secrets' in data
        assert data['custom_secrets'] == []


@pytest.mark.asyncio
async def test_add_custom_secret(test_client):
    """Test adding a new custom secret."""

    with patch_file_settings_store() as file_settings_store:
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the POST request to add a custom secret
        add_secret_data = {
            'custom_secrets': {
                'API_KEY': {'secret': 'api-key-value', 'description': 'api-key-value'}
            }
        }
        response = test_client.post('/api/secrets', json=add_secret_data)
        assert response.status_code == 200

        # Verify that the settings were stored with the new secret
        stored_settings = await file_settings_store.load()

        # Check that the secret was added
        assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'API_KEY'
            ].secret.get_secret_value()
            == 'api-key-value'
        )

    # Check that other settings were preserved
    assert stored_settings.language == 'en'
    assert stored_settings.agent == 'test-agent'
    assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'


@pytest.mark.asyncio
async def test_update_existing_custom_secret(test_client):
    """Test updating an existing custom secret."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with a custom secret
        custom_secrets = {
            'API_KEY': CustomSecret(
                secret=SecretStr('old-api-key'), description='old key'
            )
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Patch the convert_to_settings function to handle Settings objects
        with patch(
            'openhands.server.routes.settings.convert_to_settings',
            side_effect=lambda x: x,
        ):
            # Make the PUT request to update the custom secret
            update_secret_data = {
                'custom_secrets': {
                    'API_KEY': {'secret': 'new-api-key', 'desciption': 'my new key'}
                }
            }
            response = test_client.put('/api/secrets/API_KEY', json=update_secret_data)
            assert response.status_code == 200

        # Verify that the settings were stored with the updated secret
        stored_settings = await file_settings_store.load()

        # Check that the secret was updated
        assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'API_KEY'
            ].secret.get_secret_value()
            == 'new-api-key'
        )

        # Check that other settings were preserved
        assert stored_settings.language == 'en'
        assert stored_settings.agent == 'test-agent'
        assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_add_multiple_custom_secrets(test_client):
    """Test adding multiple custom secrets at once."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with one custom secret
        custom_secrets = {
            'EXISTING_SECRET': CustomSecret(
                secret=SecretStr('existing-value'), description='existing secret'
            )
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the POST request to add multiple custom secrets
        add_secrets_data = {
            'custom_secrets': {
                'API_KEY': {'secret': 'api-key-value', 'description': 'addition key'},
                'DB_PASSWORD': {
                    'secret': 'db-password-value',
                    'description': 'db password access',
                },
            }
        }
        response = test_client.post('/api/secrets', json=add_secrets_data)
        assert response.status_code == 200

        # Verify that the settings were stored with the new secrets
        stored_settings = await file_settings_store.load()

        # Check that the new secrets were added
        assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'API_KEY'
            ].secret.get_secret_value()
            == 'api-key-value'
        )
        assert 'DB_PASSWORD' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'DB_PASSWORD'
            ].secret.get_secret_value()
            == 'db-password-value'
        )

        # Check that existing secrets were preserved
        assert 'EXISTING_SECRET' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'EXISTING_SECRET'
            ].secret.get_secret_value()
            == 'existing-value'
        )

        # Check that other settings were preserved
        assert stored_settings.language == 'en'
        assert stored_settings.agent == 'test-agent'
        assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_delete_custom_secret(test_client):
    """Test deleting a custom secret."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with multiple custom secrets
        custom_secrets = {
            'API_KEY': CustomSecret(
                secret=SecretStr('api-key-value'), description='api key value'
            ),
            'DB_PASSWORD': CustomSecret(
                secret=SecretStr('db-password-value'), description='db access'
            ),
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the DELETE request to delete a custom secret
        response = test_client.delete('/api/secrets/API_KEY')
        assert response.status_code == 200

        # Verify that the settings were stored without the deleted secret
        stored_settings = await file_settings_store.load()

        # Check that the specified secret was deleted
        assert 'API_KEY' not in stored_settings.secrets_store.custom_secrets

        # Check that other secrets were preserved
        assert 'DB_PASSWORD' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'DB_PASSWORD'
            ].secret.get_secret_value()
            == 'db-password-value'
        )

        # Check that other settings were preserved
        assert stored_settings.language == 'en'
        assert stored_settings.agent == 'test-agent'
        assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_delete_nonexistent_custom_secret(test_client):
    """Test deleting a custom secret that doesn't exist."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with a custom secret
        custom_secrets = {
            'API_KEY': CustomSecret(
                secret=SecretStr('api-key-value'), description='api key value'
            )
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # Make the DELETE request to delete a nonexistent custom secret
        response = test_client.delete('/api/secrets/NONEXISTENT_KEY')
        assert response.status_code == 404
        assert 'error' in response.json()
        assert 'not found' in response.json()['error']

        # Verify that the settings were not modified
        stored_settings = await file_settings_store.load()

        # Check that the existing secret was preserved
        assert 'API_KEY' in stored_settings.secrets_store.custom_secrets
        assert (
            stored_settings.secrets_store.custom_secrets[
                'API_KEY'
            ].secret.get_secret_value()
            == 'api-key-value'
        )

        # Check that other settings were preserved
        assert stored_settings.language == 'en'
        assert stored_settings.agent == 'test-agent'
        assert stored_settings.llm_api_key.get_secret_value() == 'test-llm-key'
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens


@pytest.mark.asyncio
async def test_custom_secrets_operations_preserve_settings(test_client):
    """Test that operations on custom secrets preserve all other settings."""
    with patch_file_settings_store() as file_settings_store:
        # Create initial settings with comprehensive data
        custom_secrets = {
            'INITIAL_SECRET': CustomSecret(
                secret=SecretStr('initial-value'), description='initial env'
            )
        }
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

        # Store the initial settings
        await file_settings_store.store(initial_settings)

        # 1. Test adding a new custom secret
        add_secret_data = {
            'custom_secrets': {
                'NEW_SECRET': {
                    'secret': 'new-value',
                    'description': 'new value description',
                }
            }
        }
        response = test_client.post('/api/secrets', json=add_secret_data)
        assert response.status_code == 200

        # Verify all settings are preserved
        stored_settings = await file_settings_store.load()
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
        assert ProviderType.GITHUB in stored_settings.secrets_store.provider_tokens
        assert ProviderType.GITLAB in stored_settings.secrets_store.provider_tokens
        assert (
            stored_settings.secrets_store.custom_secrets[
                'INITIAL_SECRET'
            ].secret.get_secret_value()
            == 'initial-value'
        )
        assert (
            stored_settings.secrets_store.custom_secrets[
                'NEW_SECRET'
            ].secret.get_secret_value()
            == 'new-value'
        )

        # 2. Test updating an existing custom secret
        with patch(
            'openhands.server.routes.settings.convert_to_settings',
            side_effect=lambda x: x,
        ):
            update_secret_data = {
                'custom_secrets': {
                    'UPDATED_SECRET': {
                        'secret': 'updated-value',
                        'description': 'updated desc',
                    }
                }
            }
            response = test_client.put(
                '/api/secrets/INITIAL_SECRET', json=update_secret_data
            )
            assert response.status_code == 200

        # Verify all settings are still preserved
        stored_settings = await file_settings_store.load()
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

    # Create a new patch_file_settings_store context with updated settings
    with patch_file_settings_store() as file_settings_store:
        # Set up the updated settings
        updated_custom_secrets = {
            'UPDATED_SECRET': CustomSecret(
                secret=SecretStr('updated-value'), description='updated secret'
            ),
            'NEW_SECRET': CustomSecret(
                secret=SecretStr('new-value'), description='new secret'
            ),
        }
        updated_secret_store = SecretStore(
            custom_secrets=updated_custom_secrets, provider_tokens=provider_tokens
        )
        updated_settings = Settings(
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
            secrets_store=updated_secret_store,
        )

        # Store the updated settings
        await file_settings_store.store(updated_settings)

        # 3. Test deleting a custom secret
        response = test_client.delete('/api/secrets/NEW_SECRET')
        assert response.status_code == 200

        # Verify all settings are still preserved
        stored_settings = await file_settings_store.load()
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
