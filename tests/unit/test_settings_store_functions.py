from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from openhands.integrations.provider import ProviderToken, SecretStore
from openhands.integrations.service_types import ProviderType
from openhands.server.routes.settings import (
    check_provider_tokens,
    store_llm_settings,
    store_provider_tokens,
)
from openhands.server.settings import POSTSettingsModel
from openhands.storage.data_models.settings import Settings


# Mock functions to simulate the actual functions in settings.py
async def get_settings_store(request):
    """Mock function to get settings store."""
    return MagicMock()


# Tests for check_provider_tokens
@pytest.mark.asyncio
async def test_check_provider_tokens_valid():
    """Test check_provider_tokens with valid tokens."""
    settings = POSTSettingsModel(provider_tokens={'github': 'valid-token'})

    # Mock the validate_provider_token function to return GITHUB for valid tokens
    with patch(
        'openhands.server.routes.settings.validate_provider_token'
    ) as mock_validate:
        mock_validate.return_value = ProviderType.GITHUB

        result = await check_provider_tokens(settings)

        # Should return empty string for valid token
        assert result == ''
        mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_check_provider_tokens_invalid():
    """Test check_provider_tokens with invalid tokens."""
    settings = POSTSettingsModel(provider_tokens={'github': 'invalid-token'})

    # Mock the validate_provider_token function to return None for invalid tokens
    with patch(
        'openhands.server.routes.settings.validate_provider_token'
    ) as mock_validate:
        mock_validate.return_value = None

        result = await check_provider_tokens(settings)

        # Should return error message for invalid token
        assert 'Invalid token' in result
        mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_check_provider_tokens_wrong_type():
    """Test check_provider_tokens with unsupported provider type."""
    settings = POSTSettingsModel(provider_tokens={'unsupported': 'some-token'})

    result = await check_provider_tokens(settings)

    # Should return empty string for unsupported provider
    assert result == ''


@pytest.mark.asyncio
async def test_check_provider_tokens_no_tokens():
    """Test check_provider_tokens with no tokens."""
    settings = POSTSettingsModel(provider_tokens={})

    result = await check_provider_tokens(settings)

    # Should return empty string when no tokens provided
    assert result == ''


# Tests for store_llm_settings
@pytest.mark.asyncio
async def test_store_llm_settings_new_settings():
    """Test store_llm_settings with new settings."""
    settings = POSTSettingsModel(
        llm_model='gpt-4',
        llm_api_key='test-api-key',
        llm_base_url='https://api.example.com',
    )

    # Mock the settings store
    mock_store = MagicMock()
    mock_store.load = AsyncMock(return_value=None)  # No existing settings

    result = await store_llm_settings(settings, mock_store)

    # Should return settings with the provided values
    assert result.llm_model == 'gpt-4'
    assert result.llm_api_key.get_secret_value() == 'test-api-key'
    assert result.llm_base_url == 'https://api.example.com'


@pytest.mark.asyncio
async def test_store_llm_settings_update_existing():
    """Test store_llm_settings updates existing settings."""
    settings = POSTSettingsModel(
        llm_model='gpt-4',
        llm_api_key='new-api-key',
        llm_base_url='https://new.example.com',
    )

    # Mock the settings store
    mock_store = MagicMock()

    # Create existing settings
    existing_settings = Settings(
        llm_model='gpt-3.5',
        llm_api_key=SecretStr('old-api-key'),
        llm_base_url='https://old.example.com',
    )

    mock_store.load = AsyncMock(return_value=existing_settings)

    result = await store_llm_settings(settings, mock_store)

    # Should return settings with the updated values
    assert result.llm_model == 'gpt-4'
    assert result.llm_api_key.get_secret_value() == 'new-api-key'
    assert result.llm_base_url == 'https://new.example.com'


@pytest.mark.asyncio
async def test_store_llm_settings_partial_update():
    """Test store_llm_settings with partial update."""
    settings = POSTSettingsModel(
        llm_model='gpt-4'  # Only updating model
    )

    # Mock the settings store
    mock_store = MagicMock()

    # Create existing settings
    existing_settings = Settings(
        llm_model='gpt-3.5',
        llm_api_key=SecretStr('existing-api-key'),
        llm_base_url='https://existing.example.com',
    )

    mock_store.load = AsyncMock(return_value=existing_settings)

    result = await store_llm_settings(settings, mock_store)

    # Should return settings with updated model but keep other values
    assert result.llm_model == 'gpt-4'
    # For SecretStr objects, we need to compare the secret value
    assert result.llm_api_key.get_secret_value() == 'existing-api-key'
    assert result.llm_base_url == 'https://existing.example.com'


# Tests for store_provider_tokens
@pytest.mark.asyncio
async def test_store_provider_tokens_new_tokens():
    """Test store_provider_tokens with new tokens."""
    settings = POSTSettingsModel(provider_tokens={'github': 'new-token'})

    # Mock the settings store
    mock_store = MagicMock()
    mock_store.load = AsyncMock(return_value=None)  # No existing settings

    result = await store_provider_tokens(settings, mock_store)

    # Should return settings with the provided tokens
    assert result.provider_tokens == {'github': 'new-token'}


@pytest.mark.asyncio
async def test_store_provider_tokens_update_existing():
    """Test store_provider_tokens updates existing tokens."""
    settings = POSTSettingsModel(provider_tokens={'github': 'updated-token'})

    # Mock the settings store
    mock_store = MagicMock()

    # Create existing settings with a GitHub token
    github_token = ProviderToken(token=SecretStr('old-token'))
    provider_tokens = {ProviderType.GITHUB: github_token}

    # Create a SecretStore with the provider tokens
    secrets_store = SecretStore(provider_tokens=provider_tokens)

    # Create existing settings with the secrets store
    existing_settings = Settings(secrets_store=secrets_store)

    mock_store.load = AsyncMock(return_value=existing_settings)

    result = await store_provider_tokens(settings, mock_store)

    # Should return settings with the updated tokens
    assert result.provider_tokens == {'github': 'updated-token'}


@pytest.mark.asyncio
async def test_store_provider_tokens_keep_existing():
    """Test store_provider_tokens keeps existing tokens when empty string provided."""
    settings = POSTSettingsModel(
        provider_tokens={'github': ''}  # Empty string should keep existing token
    )

    # Mock the settings store
    mock_store = MagicMock()

    # Create existing settings with a GitHub token
    github_token = ProviderToken(token=SecretStr('existing-token'))
    provider_tokens = {ProviderType.GITHUB: github_token}

    # Create a SecretStore with the provider tokens
    secrets_store = SecretStore(provider_tokens=provider_tokens)

    # Create existing settings with the secrets store
    existing_settings = Settings(secrets_store=secrets_store)

    mock_store.load = AsyncMock(return_value=existing_settings)

    result = await store_provider_tokens(settings, mock_store)

    # Should return settings with the existing token preserved
    assert result.provider_tokens == {'github': 'existing-token'}
