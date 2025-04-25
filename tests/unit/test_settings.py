from unittest.mock import call, mock, patch

import pytest
from pydantic import SecretStr
from pytest import mark

from openhands.core.config.app_config import AppConfig
from openhands.core.config.config_save import save_setting_to_user_toml
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig
from openhands.integrations.provider import ProviderToken, ProviderType, SecretStore
from openhands.server.routes.settings import convert_to_settings
from openhands.server.settings import POSTSettingsModel, Settings
from openhands.storage.settings.file_settings_store import (
    SECRETS_STORE_TO_APPCONFIG_MAP,
    SETTINGS_TO_APPCONFIG_MAP,
    FileSettingsStore,
)
from openhands.utils.async_utils import call_sync_from_async


def test_settings_from_config():
    # Mock configuration
    mock_app_config = AppConfig(
        default_agent='test-agent',
        max_iterations=100,
        security=SecurityConfig(
            security_analyzer='test-analyzer', confirmation_mode=True
        ),
        llms={
            'llm': LLMConfig(
                model='test-model',
                api_key=SecretStr('test-key'),
                base_url='https://test.example.com',
            )
        },
        sandbox=SandboxConfig(remote_runtime_resource_factor=2),
    )

    with patch(
        'openhands.server.settings.load_app_config', return_value=mock_app_config
    ):
        settings = Settings.from_config()

        assert settings is not None
        assert settings.language == 'en'
        assert settings.agent == 'test-agent'
        assert settings.max_iterations == 100
        assert settings.security_analyzer == 'test-analyzer'
        assert settings.confirmation_mode is True
        assert settings.llm_model == 'test-model'
        assert settings.llm_api_key.get_secret_value() == 'test-key'
        assert settings.llm_base_url == 'https://test.example.com'
        assert settings.remote_runtime_resource_factor == 2
        assert not settings.secrets_store.provider_tokens


def test_settings_from_config_no_api_key():
    # Mock configuration without API key
    mock_app_config = AppConfig(
        default_agent='test-agent',
        max_iterations=100,
        security=SecurityConfig(
            security_analyzer='test-analyzer', confirmation_mode=True
        ),
        llms={
            'llm': LLMConfig(
                model='test-model', api_key=None, base_url='https://test.example.com'
            )
        },
        sandbox=SandboxConfig(remote_runtime_resource_factor=2),
    )

    with patch(
        'openhands.server.settings.load_app_config', return_value=mock_app_config
    ):
        settings = Settings.from_config()
        assert settings is None


def test_settings_handles_sensitive_data():
    settings = Settings(
        language='en',
        agent='test-agent',
        max_iterations=100,
        security_analyzer='test-analyzer',
        confirmation_mode=True,
        llm_model='test-model',
        llm_api_key='test-key',
        llm_base_url='https://test.example.com',
        remote_runtime_resource_factor=2,
        secrets_store=SecretStore(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(
                    token=SecretStr('test-token'),
                    user_id=None,
                )
            }
        ),
    )

    assert str(settings.llm_api_key) == '**********'
    assert (
        str(settings.secrets_store.provider_tokens[ProviderType.GITHUB].token)
        == '**********'
    )

    assert settings.llm_api_key.get_secret_value() == 'test-key'
    assert (
        settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test-token'
    )


# =============================================
# Tests for FileSettingsStore (New)
# =============================================


@pytest.fixture
def mock_app_config():
    """Provides a mock AppConfig instance for testing FileSettingsStore."""
    # Create a base config with some values
    config = AppConfig(
        default_agent='CodeActAgent',
        max_iterations=50,
        llms={
            'llm': LLMConfig(
                model='gpt-4',
                api_key=SecretStr('existing_key'),
                base_url='existing_url',
            )
        },
        security=SecurityConfig(confirmation_mode=False),
        sandbox=SandboxConfig(base_container_image='image1'),
    )
    # Set a dummy snapshot (tests for save logic are in test_config_write.py)
    config.set_toml_snapshot(config.model_copy(deep=True))
    return config


@pytest.fixture
async def file_settings_store_instance(mock_app_config):
    """Provides an initialized FileSettingsStore instance."""
    # Note: user_id is currently unused by FileSettingsStore.get_instance
    return await FileSettingsStore.get_instance(mock_app_config, user_id='test_user')


@mark.asyncio
async def test_file_settings_store_load(file_settings_store_instance, mock_app_config):
    """Test loading settings reconstructs Settings from AppConfig."""
    # Arrange (AppConfig is already set in the fixture)

    # Act
    loaded_settings = await file_settings_store_instance.load()

    # Assert
    assert loaded_settings is not None
    assert loaded_settings.agent == mock_app_config.default_agent
    assert loaded_settings.max_iterations == mock_app_config.max_iterations
    assert loaded_settings.llm_model == mock_app_config.llm.model
    assert loaded_settings.llm_api_key == mock_app_config.llm.api_key
    assert loaded_settings.llm_base_url == mock_app_config.llm.base_url
    assert (
        loaded_settings.confirmation_mode == mock_app_config.security.confirmation_mode
    )
    assert (
        loaded_settings.sandbox_base_container_image
        == mock_app_config.sandbox.base_container_image
    )
    # Check a field not present in mock_app_config (should be None or default)
    assert loaded_settings.security_analyzer is None  # Assuming it wasn't set
    # Secrets store is currently basic in load
    assert isinstance(loaded_settings.secrets_store, SecretStore)


@mark.asyncio
@patch('openhands.storage.settings.file_settings_store.save_setting_to_user_toml')
async def test_file_settings_store_store_general_settings(
    mock_save_setting, file_settings_store_instance, mock_app_config
):
    """Test storing general settings calls save_setting_to_user_toml correctly."""
    # Arrange
    settings_to_store = Settings(
        agent='NewAgent',  # Mapped
        llm_model='new-model',  # Mapped
        llm_api_key=SecretStr('new-key'),  # Mapped
        language='fr',  # Not mapped
        secrets_store=SecretStore(),  # Excluded from general loop
    )

    # Act
    await file_settings_store_instance.store(settings_to_store)

    # Assert
    expected_calls = [
        call(mock_app_config, SETTINGS_TO_APPCONFIG_MAP['agent'], 'NewAgent'),
        call(mock_app_config, SETTINGS_TO_APPCONFIG_MAP['llm_model'], 'new-model'),
        call(
            mock_app_config,
            SETTINGS_TO_APPCONFIG_MAP['llm_api_key'],
            'new-key',  # Raw string
        ),
        # Note: language is not mapped, so it shouldn't be called
    ]
    # We need to wrap the sync function call for mocking async context
    call_sync_from_async(save_setting_to_user_toml)

    # Check calls made via call_sync_from_async
    # This requires inspecting the arguments passed to call_sync_from_async
    # A direct mock on save_setting_to_user_toml might be simpler if call_sync_from_async is reliable
    # Let's assume direct mock works for simplicity here, adjust if needed based on execution flow.
    mock_save_setting.assert_has_calls(expected_calls, any_order=True)
    assert mock_save_setting.call_count == 3  # Only mapped fields


@mark.asyncio
@patch('openhands.storage.settings.file_settings_store.save_setting_to_user_toml')
async def test_file_settings_store_store_secrets(
    mock_save_setting, file_settings_store_instance, mock_app_config
):
    """Test storing secrets calls save_setting_to_user_toml correctly."""
    # Arrange
    github_token = 'ghp_test123'
    custom_key = 'custom_value_abc'
    custom_secret_name = 'MY_CUSTOM_API_KEY'

    settings_to_store = Settings(
        secrets_store=SecretStore(
            provider_tokens={
                ProviderType.GITHUB: ProviderToken(token=SecretStr(github_token))
            },
            custom_secrets={custom_secret_name: SecretStr(custom_key)},
        )
    )

    # Act
    await file_settings_store_instance.store(settings_to_store)

    # Assert
    token_base_path = SECRETS_STORE_TO_APPCONFIG_MAP['provider_tokens']
    custom_base_path = SECRETS_STORE_TO_APPCONFIG_MAP['custom_secrets']

    expected_calls = [
        mock.call(
            mock_app_config,
            f'{token_base_path}.{ProviderType.GITHUB.value}',
            github_token,  # Raw string
        ),
        mock.call(
            mock_app_config,
            f'{custom_base_path}.{custom_secret_name}',
            custom_key,  # Raw string
        ),
    ]
    mock_save_setting.assert_has_calls(expected_calls, any_order=True)
    assert mock_save_setting.call_count == 2  # Only secrets in this test case


def test_convert_to_settings():
    settings_with_token_data = POSTSettingsModel(
        llm_api_key='test-key',
        provider_tokens={
            'github': 'test-token',
        },
    )

    settings = convert_to_settings(settings_with_token_data)

    assert settings.llm_api_key.get_secret_value() == 'test-key'
    assert (
        settings.secrets_store.provider_tokens[
            ProviderType.GITHUB
        ].token.get_secret_value()
        == 'test-token'
    )
