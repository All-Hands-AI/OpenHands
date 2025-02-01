from unittest.mock import patch

from pydantic import SecretStr

from openhands.core.config.app_config import AppConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.sandbox_config import SandboxConfig
from openhands.core.config.security_config import SecurityConfig
from openhands.server.routes.settings import convert_to_settings
from openhands.server.settings import POSTSettingsModel, Settings


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
        assert settings.github_token is None


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
        github_token='test-token',
    )

    assert str(settings.llm_api_key) == '**********'
    assert str(settings.github_token) == '**********'

    assert settings.llm_api_key.get_secret_value() == 'test-key'
    assert settings.github_token.get_secret_value() == 'test-token'


def test_convert_to_settings():
    settings_with_token_data = POSTSettingsModel(
        llm_api_key='test-key',
        github_token='test-token',
    )

    settings = convert_to_settings(settings_with_token_data)

    assert settings.llm_api_key.get_secret_value() == 'test-key'
    assert settings.github_token.get_secret_value() == 'test-token'
