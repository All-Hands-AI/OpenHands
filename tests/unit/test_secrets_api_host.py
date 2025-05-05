"""Tests for the secrets API with host parameter."""

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
async def test_add_git_providers_with_host(test_client, file_secrets_store):
    """Test adding git providers with host parameter."""
    # Create initial user secrets
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(provider_tokens=provider_tokens)
    await file_secrets_store.store(user_secrets)

    # Mock check_provider_tokens to return empty string (no error)
    with patch(
        'openhands.server.routes.secrets.check_provider_tokens',
        AsyncMock(return_value=''),
    ):
        # Add a GitHub provider with a host
        add_provider_data = {
            'provider_tokens': {
                'github': {'token': 'new-github-token', 'host': 'github.enterprise.com'}
            }
        }
        response = test_client.post('/api/add-git-providers', json=add_provider_data)
        assert response.status_code == 200

        # Verify that the settings were stored with the new provider token and host
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'new-github-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].host
            == 'github.enterprise.com'
        )


@pytest.mark.asyncio
async def test_add_git_providers_update_host_only(test_client, file_secrets_store):
    """Test updating only the host for an existing provider token."""
    # Create initial user secrets with a token
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(
            token=SecretStr('github-token'), host='github.com'
        )
    }
    user_secrets = UserSecrets(provider_tokens=provider_tokens)
    await file_secrets_store.store(user_secrets)

    # Mock check_provider_tokens to return empty string (no error)
    with patch(
        'openhands.server.routes.secrets.check_provider_tokens',
        AsyncMock(return_value=''),
    ):
        # Update only the host
        update_host_data = {
            'provider_tokens': {
                'github': {
                    'token': '',  # Empty token means keep existing token
                    'host': 'github.enterprise.com',
                }
            }
        }
        response = test_client.post('/api/add-git-providers', json=update_host_data)
        assert response.status_code == 200

        # Verify that the host was updated but the token remains the same
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].host
            == 'github.enterprise.com'
        )


@pytest.mark.asyncio
async def test_add_git_providers_invalid_token_with_host(
    test_client, file_secrets_store
):
    """Test adding an invalid token with a host."""
    # Create initial user secrets
    user_secrets = UserSecrets()
    await file_secrets_store.store(user_secrets)

    # Mock validate_provider_token to return None (invalid token)
    with patch(
        'openhands.integrations.utils.validate_provider_token',
        AsyncMock(return_value=None),
    ):
        # Try to add an invalid GitHub provider with a host
        add_provider_data = {
            'provider_tokens': {
                'github': {'token': 'invalid-token', 'host': 'github.enterprise.com'}
            }
        }
        response = test_client.post('/api/add-git-providers', json=add_provider_data)
        assert response.status_code == 401
        assert 'Invalid token' in response.json()['error']


@pytest.mark.asyncio
async def test_add_multiple_git_providers_with_hosts(test_client, file_secrets_store):
    """Test adding multiple git providers with different hosts."""
    # Create initial user secrets
    user_secrets = UserSecrets()
    await file_secrets_store.store(user_secrets)

    # Mock check_provider_tokens to return empty string (no error)
    with patch(
        'openhands.server.routes.secrets.check_provider_tokens',
        AsyncMock(return_value=''),
    ):
        # Add multiple providers with hosts
        add_providers_data = {
            'provider_tokens': {
                'github': {'token': 'github-token', 'host': 'github.enterprise.com'},
                'gitlab': {'token': 'gitlab-token', 'host': 'gitlab.enterprise.com'},
            }
        }
        response = test_client.post('/api/add-git-providers', json=add_providers_data)
        assert response.status_code == 200

        # Verify that both providers were stored with their respective hosts
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'github-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].host
            == 'github.enterprise.com'
        )

        assert ProviderType.GITLAB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITLAB].token.get_secret_value()
            == 'gitlab-token'
        )
        assert (
            stored_secrets.provider_tokens[ProviderType.GITLAB].host
            == 'gitlab.enterprise.com'
        )
