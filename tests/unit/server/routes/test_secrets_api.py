"""Tests for the custom secrets API endpoints."""
# flake8: noqa: E501

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from openhands.integrations.provider import (
    CustomSecret,
    ProviderToken,
    ProviderType,
)
from openhands.server.routes.secrets import (
    app as secrets_app,
)
from openhands.server.routes.secrets import (
    get_provider_from_url,
    update_url_with_token,
)
from openhands.storage import get_file_store
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.file_secrets_store import FileSecretsStore


@pytest.fixture
def test_client():
    """Create a test client for the settings API."""
    app = FastAPI()
    app.include_router(secrets_app)

    # Mock SESSION_API_KEY to None to disable authentication in tests
    with patch.dict(os.environ, {'SESSION_API_KEY': ''}, clear=False):
        # Clear the SESSION_API_KEY to disable auth dependency
        with patch('openhands.server.dependencies._SESSION_API_KEY', None):
            yield TestClient(app)


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
        'API_KEY': CustomSecret(secret=SecretStr('api-key-value')),
        'DB_PASSWORD': CustomSecret(secret=SecretStr('db-password-value')),
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
    print(response)
    assert response.status_code == 200

    # Check the response
    data = response.json()
    assert 'custom_secrets' in data
    # Extract just the names from the list of custom secrets
    secret_names = [secret['name'] for secret in data['custom_secrets']]
    assert sorted(secret_names) == ['API_KEY', 'DB_PASSWORD']

    # Verify that the original settings were not modified
    stored_settings = await file_secrets_store.load()
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].secret.get_secret_value()
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
    user_secrets = UserSecrets(provider_tokens=provider_tokens, custom_secrets={})

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
    add_secret_data = {'name': 'API_KEY', 'value': 'api-key-value', 'description': None}
    response = test_client.post('/api/secrets', json=add_secret_data)
    assert response.status_code == 201

    # Verify that the settings were stored with the new secret
    stored_settings = await file_secrets_store.load()

    # Check that the secret was added
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )


@pytest.mark.asyncio
async def test_create_custom_secret_with_no_existing_secrets(
    test_client, file_secrets_store
):
    """Test creating a custom secret when there are no existing secrets at all."""
    # Don't store any initial settings - this simulates a completely new user
    # or a situation where the secrets store is empty

    # Make the POST request to add a custom secret
    add_secret_data = {
        'name': 'NEW_API_KEY',
        'value': 'new-api-key-value',
        'description': 'Test API Key',
    }
    response = test_client.post('/api/secrets', json=add_secret_data)
    assert response.status_code == 201

    # Verify that the settings were stored with the new secret
    stored_settings = await file_secrets_store.load()

    # Check that the secret was added
    assert 'NEW_API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['NEW_API_KEY'].secret.get_secret_value()
        == 'new-api-key-value'
    )
    assert stored_settings.custom_secrets['NEW_API_KEY'].description == 'Test API Key'

    # Check that provider_tokens is an empty dict, not None
    assert stored_settings.provider_tokens == {}


@pytest.mark.asyncio
async def test_update_existing_custom_secret(test_client, file_secrets_store):
    """Test updating an existing custom secret's name and description (cannot change value once set)."""
    # Create initial settings with a custom secret
    custom_secrets = {'API_KEY': CustomSecret(secret=SecretStr('old-api-key'))}
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the PUT request to update the custom secret
    update_secret_data = {
        'name': 'API_KEY',
        'description': None,
    }
    response = test_client.put('/api/secrets/API_KEY', json=update_secret_data)
    assert response.status_code == 200

    # Verify that the settings were stored with the updated secret
    stored_settings = await file_secrets_store.load()

    # Check that the secret was updated
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'old-api-key'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_add_multiple_custom_secrets(test_client, file_secrets_store):
    """Test adding multiple custom secrets at once."""
    # Create initial settings with one custom secret
    custom_secrets = {
        'EXISTING_SECRET': CustomSecret(secret=SecretStr('existing-value'))
    }
    provider_tokens = {
        ProviderType.GITHUB: ProviderToken(token=SecretStr('github-token'))
    }
    user_secrets = UserSecrets(
        custom_secrets=custom_secrets, provider_tokens=provider_tokens
    )

    # Store the initial settings
    await file_secrets_store.store(user_secrets)

    # Make the POST request to add first custom secret
    add_secret_data1 = {
        'name': 'API_KEY',
        'value': 'api-key-value',
        'description': None,
    }
    response1 = test_client.post('/api/secrets', json=add_secret_data1)
    assert response1.status_code == 201

    # Make the POST request to add second custom secret
    add_secret_data2 = {
        'name': 'DB_PASSWORD',
        'value': 'db-password-value',
        'description': None,
    }
    response = test_client.post('/api/secrets', json=add_secret_data2)
    assert response.status_code == 201

    # Verify that the settings were stored with the new secrets
    stored_settings = await file_secrets_store.load()

    # Check that the new secrets were added
    assert 'API_KEY' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )
    assert 'DB_PASSWORD' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['DB_PASSWORD'].secret.get_secret_value()
        == 'db-password-value'
    )

    # Check that existing secrets were preserved
    assert 'EXISTING_SECRET' in stored_settings.custom_secrets
    assert (
        stored_settings.custom_secrets['EXISTING_SECRET'].secret.get_secret_value()
        == 'existing-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_delete_custom_secret(test_client, file_secrets_store):
    """Test deleting a custom secret."""
    # Create initial settings with multiple custom secrets
    custom_secrets = {
        'API_KEY': CustomSecret(secret=SecretStr('api-key-value')),
        'DB_PASSWORD': CustomSecret(secret=SecretStr('db-password-value')),
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
        stored_settings.custom_secrets['DB_PASSWORD'].secret.get_secret_value()
        == 'db-password-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


@pytest.mark.asyncio
async def test_delete_nonexistent_custom_secret(test_client, file_secrets_store):
    """Test deleting a custom secret that doesn't exist."""
    # Create initial settings with a custom secret
    custom_secrets = {
        'API_KEY': CustomSecret(secret=SecretStr('api-key-value'), description='')
    }
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
        stored_settings.custom_secrets['API_KEY'].secret.get_secret_value()
        == 'api-key-value'
    )

    # Check that other settings were preserved
    assert ProviderType.GITHUB in stored_settings.provider_tokens


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


# =================================================
# SECTION: Tests for git URL helper functions
# =================================================


def test_get_provider_from_url_github():
    """Test extracting GitHub provider from various URL formats."""
    assert get_provider_from_url('https://github.com/owner/repo') == ProviderType.GITHUB
    assert (
        get_provider_from_url('https://token@github.com/owner/repo')
        == ProviderType.GITHUB
    )
    assert (
        get_provider_from_url('https://x-access-token:token@github.com/owner/repo')
        == ProviderType.GITHUB
    )
    assert get_provider_from_url('git@github.com:owner/repo.git') == ProviderType.GITHUB


def test_get_provider_from_url_gitlab():
    """Test extracting GitLab provider from various URL formats."""
    assert get_provider_from_url('https://gitlab.com/owner/repo') == ProviderType.GITLAB
    assert (
        get_provider_from_url('https://oauth2:token@gitlab.com/owner/repo')
        == ProviderType.GITLAB
    )
    assert get_provider_from_url('git@gitlab.com:owner/repo.git') == ProviderType.GITLAB


def test_get_provider_from_url_bitbucket():
    """Test extracting Bitbucket provider from various URL formats."""
    assert (
        get_provider_from_url('https://bitbucket.org/owner/repo')
        == ProviderType.BITBUCKET
    )
    assert (
        get_provider_from_url('https://x-token-auth:token@bitbucket.org/owner/repo')
        == ProviderType.BITBUCKET
    )
    assert (
        get_provider_from_url('git@bitbucket.org:owner/repo.git')
        == ProviderType.BITBUCKET
    )


def test_get_provider_from_url_unknown():
    """Test that unknown providers return None."""
    assert get_provider_from_url('https://example.com/owner/repo') is None
    assert get_provider_from_url('https://custom-git-server.com/repo') is None
    assert get_provider_from_url('') is None
    assert get_provider_from_url('not-a-url') is None


def test_update_url_with_token_github():
    """Test updating GitHub URL with new token - actual logic testing."""
    # Test standard GitHub format with old token
    old_url = 'https://old_token@github.com/owner/repo.git'
    new_url = update_url_with_token(old_url, ProviderType.GITHUB, 'new_token')
    assert new_url == 'https://new_token@github.com/owner/repo.git'
    # Verify the actual string replacement worked correctly
    assert 'old_token' not in new_url
    assert 'new_token' in new_url

    # Test x-access-token format (should be normalized to simple token format)
    old_url = 'https://x-access-token:old_token@github.com/owner/repo.git'
    new_url = update_url_with_token(old_url, ProviderType.GITHUB, 'new_token')
    assert new_url == 'https://new_token@github.com/owner/repo.git'
    assert 'old_token' not in new_url
    assert 'new_token' in new_url

    # Test URL without token (no credentials)
    url_without_token = 'https://github.com/owner/repo.git'
    # Should still work - adds token to URL
    result = update_url_with_token(url_without_token, ProviderType.GITHUB, 'new_token')
    # This URL has no credentials, so regex won't match and URL returns unchanged
    assert result == url_without_token


def test_update_url_with_token_gitlab():
    """Test updating GitLab URL with new token - actual logic testing."""
    # Test GitLab oauth2 format
    old_url = 'https://oauth2:old_token@gitlab.com/owner/repo.git'
    new_url = update_url_with_token(old_url, ProviderType.GITLAB, 'new_token')
    assert new_url == 'https://oauth2:new_token@gitlab.com/owner/repo.git'
    # Verify the actual replacement
    assert 'old_token' not in new_url
    assert 'oauth2:new_token' in new_url


def test_update_url_with_token_bitbucket():
    """Test updating Bitbucket URL with new token - actual logic testing."""
    # Test Bitbucket x-token-auth format
    old_url = 'https://x-token-auth:old_token@bitbucket.org/owner/repo.git'
    new_url = update_url_with_token(old_url, ProviderType.BITBUCKET, 'new_token')
    assert new_url == 'https://x-token-auth:new_token@bitbucket.org/owner/repo.git'
    # Verify the actual replacement
    assert 'old_token' not in new_url
    assert 'x-token-auth:new_token' in new_url


def test_update_url_with_token_unsupported_provider():
    """Test that unsupported providers return URL unchanged."""
    url = 'https://token@example.com/owner/repo.git'
    # Using GITHUB for an example.com URL should not modify it
    # Actually, it might - let's test with an unknown provider scenario
    # The function doesn't handle unknown providers, so it returns unchanged
    # Let's verify the actual behavior for each provider on wrong URLs
    result = update_url_with_token(url, ProviderType.GITHUB, 'new_token')
    # Should return unchanged since URL doesn't match github.com pattern
    assert result == url


def test_update_url_with_token_preserves_path():
    """Test that URL path and .git suffix are preserved correctly."""
    old_url = 'https://old_token@github.com/owner/repo-name.git'
    new_url = update_url_with_token(old_url, ProviderType.GITHUB, 'new_token')
    # Verify path is preserved
    assert 'owner/repo-name.git' in new_url
    assert new_url == 'https://new_token@github.com/owner/repo-name.git'


@pytest.mark.asyncio
async def test_add_git_providers_updates_git_remote_urls(
    test_client, file_secrets_store
):
    """Test that adding git providers calls git URL update logic - tests endpoint integration."""
    # Create initial user secrets
    user_secrets = UserSecrets()
    await file_secrets_store.store(user_secrets)

    # Mock the external dependencies but test our real endpoint logic
    with (
        patch(
            'openhands.server.routes.secrets.check_provider_tokens',
            AsyncMock(return_value=''),
        ),
        patch('openhands.server.routes.secrets.os.walk') as mock_walk,
        patch('openhands.server.routes.secrets.os.path.exists', return_value=True),
        patch('openhands.server.routes.secrets.subprocess.run') as mock_run,
    ):
        # Simulate finding one git repo in workspace
        mock_walk.return_value = [('/workspace/test-repo', ['.git'], [])]

        # Simulate git remote get-url returning a URL with old token
        mock_run.return_value = MagicMock(
            stdout='https://old_token@github.com/owner/repo.git\n',
            returncode=0,
        )

        # Add provider with new token via real endpoint
        add_provider_data = {
            'provider_tokens': {'github': {'token': 'new_token', 'host': 'github.com'}}
        }
        response = test_client.post('/api/add-git-providers', json=add_provider_data)
        assert response.status_code == 200

        # Verify the tokens were stored (real store interaction)
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert (
            stored_secrets.provider_tokens[ProviderType.GITHUB].token.get_secret_value()
            == 'new_token'
        )

        # Verify subprocess was called with correct git commands
        # Should have: 1) get-url call, 2) set-url call
        assert mock_run.call_count >= 2

        # Find the set-url call
        calls = [str(call) for call in mock_run.call_args_list]
        set_url_calls = [c for c in calls if 'set-url' in c]
        assert len(set_url_calls) > 0

        # Verify the new token is in the set-url command
        assert any('new_token' in call for call in set_url_calls)


@pytest.mark.asyncio
async def test_update_git_remote_urls_workspace_not_exists(
    test_client, file_secrets_store
):
    """Test that git URL update handles missing workspace gracefully."""
    user_secrets = UserSecrets()
    await file_secrets_store.store(user_secrets)

    with (
        patch(
            'openhands.server.routes.secrets.check_provider_tokens',
            AsyncMock(return_value=''),
        ),
        patch(
            'openhands.server.routes.secrets.os.path.exists', return_value=False
        ) as mock_exists,
        patch('openhands.server.routes.secrets.subprocess.run') as mock_run,
    ):
        # Add provider
        add_provider_data = {
            'provider_tokens': {'github': {'token': 'new_token', 'host': 'github.com'}}
        }
        response = test_client.post('/api/add-git-providers', json=add_provider_data)
        assert response.status_code == 200

        # Verify workspace existence was checked
        assert mock_exists.called

        # Verify subprocess was NOT called since workspace doesn't exist
        assert mock_run.call_count == 0


@pytest.mark.asyncio
async def test_update_git_remote_urls_multiple_repos(test_client, file_secrets_store):
    """Test updating multiple git repos with different providers."""
    user_secrets = UserSecrets()
    await file_secrets_store.store(user_secrets)

    with (
        patch(
            'openhands.server.routes.secrets.check_provider_tokens',
            AsyncMock(return_value=''),
        ),
        patch('openhands.server.routes.secrets.os.walk') as mock_walk,
        patch('openhands.server.routes.secrets.os.path.exists', return_value=True),
        patch('openhands.server.routes.secrets.subprocess.run') as mock_run,
    ):
        # Simulate finding two git repos
        mock_walk.return_value = [
            ('/workspace/repo1', ['.git'], []),
            ('/workspace/repo2', ['.git'], []),
        ]

        # Simulate different remotes for each repo
        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('command', [])
            if 'get-url' in cmd:
                if '/workspace/repo1' in str(cmd):
                    return MagicMock(
                        stdout='https://old_github@github.com/owner/repo1.git\n',
                        returncode=0,
                    )
                elif '/workspace/repo2' in str(cmd):
                    return MagicMock(
                        stdout='https://oauth2:old_gitlab@gitlab.com/owner/repo2.git\n',
                        returncode=0,
                    )
            return MagicMock(stdout='', returncode=0)

        mock_run.side_effect = mock_subprocess_side_effect

        # Add both providers
        add_provider_data = {
            'provider_tokens': {
                'github': {'token': 'new_github_token', 'host': 'github.com'},
                'gitlab': {'token': 'new_gitlab_token', 'host': 'gitlab.com'},
            }
        }
        response = test_client.post('/api/add-git-providers', json=add_provider_data)
        assert response.status_code == 200

        # Verify both tokens were stored
        stored_secrets = await file_secrets_store.load()
        assert ProviderType.GITHUB in stored_secrets.provider_tokens
        assert ProviderType.GITLAB in stored_secrets.provider_tokens

        # Verify subprocess was called multiple times for both repos
        assert mock_run.call_count >= 4  # At least 2 get-url + 2 set-url calls
