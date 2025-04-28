from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prompt_toolkit.formatted_text import HTML
from pydantic import SecretStr

from openhands.core.cli_settings import (
    display_settings,
    modify_llm_settings_advanced,
    modify_llm_settings_basic,
)
from openhands.core.cli_tui import UserCancelledError
from openhands.core.config import AppConfig
from openhands.storage.data_models.settings import Settings
from openhands.storage.settings.file_settings_store import FileSettingsStore


# Mock classes for condensers
class MockLLMSummarizingCondenserConfig:
    def __init__(self, llm_config, type):
        self.llm_config = llm_config
        self.type = type


class MockNoOpCondenserConfig:
    def __init__(self, type):
        self.type = type


class TestDisplaySettings:
    @pytest.fixture
    def app_config(self):
        config = MagicMock(spec=AppConfig)
        llm_config = MagicMock()
        llm_config.base_url = None
        llm_config.model = 'openai/gpt-4'
        llm_config.api_key = SecretStr('test-api-key')
        config.get_llm_config.return_value = llm_config
        config.default_agent = 'test-agent'

        # Set up security as a separate mock
        security_mock = MagicMock()
        security_mock.confirmation_mode = True
        config.security = security_mock

        config.enable_default_condenser = True
        return config

    @pytest.fixture
    def advanced_app_config(self):
        config = MagicMock(spec=AppConfig)
        llm_config = MagicMock()
        llm_config.base_url = 'https://custom-api.com'
        llm_config.model = 'custom-model'
        llm_config.api_key = SecretStr('test-api-key')
        config.get_llm_config.return_value = llm_config
        config.default_agent = 'test-agent'

        # Set up security as a separate mock
        security_mock = MagicMock()
        security_mock.confirmation_mode = True
        config.security = security_mock

        config.enable_default_condenser = True
        return config

    @patch('openhands.core.cli_settings.print_container')
    def test_display_settings_standard_config(self, mock_print_container, app_config):
        display_settings(app_config)
        mock_print_container.assert_called_once()

        # Verify the container was created with the correct settings
        container = mock_print_container.call_args[0][0]
        text_area = container.body

        # Check that the text area contains expected labels and values
        settings_text = text_area.text
        assert 'LLM Provider:' in settings_text
        assert 'openai' in settings_text
        assert 'LLM Model:' in settings_text
        assert 'gpt-4' in settings_text
        assert 'API Key:' in settings_text
        assert '********' in settings_text
        assert 'Agent:' in settings_text
        assert 'test-agent' in settings_text
        assert 'Confirmation Mode:' in settings_text
        assert 'Enabled' in settings_text
        assert 'Memory Condensation:' in settings_text
        assert 'Enabled' in settings_text

    @patch('openhands.core.cli_settings.print_container')
    def test_display_settings_advanced_config(
        self, mock_print_container, advanced_app_config
    ):
        display_settings(advanced_app_config)
        mock_print_container.assert_called_once()

        # Verify the container was created with the correct settings
        container = mock_print_container.call_args[0][0]
        text_area = container.body

        # Check that the text area contains expected labels and values
        settings_text = text_area.text
        assert 'Custom Model:' in settings_text
        assert 'custom-model' in settings_text
        assert 'Base URL:' in settings_text
        assert 'https://custom-api.com' in settings_text
        assert 'API Key:' in settings_text
        assert '********' in settings_text
        assert 'Agent:' in settings_text
        assert 'test-agent' in settings_text


class TestModifyLLMSettingsBasic:
    @pytest.fixture
    def app_config(self):
        config = MagicMock(spec=AppConfig)
        llm_config = MagicMock()
        llm_config.model = 'openai/gpt-4'
        llm_config.api_key = SecretStr('test-api-key')
        llm_config.base_url = None
        config.get_llm_config.return_value = llm_config
        config.set_llm_config = MagicMock()
        config.set_agent_config = MagicMock()

        agent_config = MagicMock()
        config.get_agent_config.return_value = agent_config

        # Set up security as a separate mock
        security_mock = MagicMock()
        security_mock.confirmation_mode = True
        config.security = security_mock

        return config

    @pytest.fixture
    def settings_store(self):
        store = MagicMock(spec=FileSettingsStore)
        store.load = AsyncMock(return_value=Settings())
        store.store = AsyncMock()
        return store

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.get_supported_llm_models')
    @patch('openhands.core.cli_settings.organize_models_and_providers')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    async def test_modify_llm_settings_basic_success(
        self,
        mock_confirm,
        mock_session,
        mock_organize,
        mock_get_models,
        app_config,
        settings_store,
    ):
        # Setup mocks
        mock_get_models.return_value = ['openai/gpt-4', 'anthropic/claude-3-opus']
        mock_organize.return_value = {
            'openai': {'models': ['gpt-4', 'gpt-3.5-turbo'], 'separator': '/'},
            'anthropic': {
                'models': ['claude-3-opus', 'claude-3-sonnet'],
                'separator': '/',
            },
        }

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(
            side_effect=[
                'openai',  # Provider
                'gpt-4',  # Model
                'new-api-key',  # API Key
            ]
        )
        mock_session.return_value = session_instance

        # Mock user confirmation
        mock_confirm.return_value = 0  # User selects "Yes, proceed"

        # Call the function
        await modify_llm_settings_basic(app_config, settings_store)

        # Verify LLM config was updated
        app_config.set_llm_config.assert_called_once()
        args, kwargs = app_config.set_llm_config.call_args
        assert args[0].model == 'openai/gpt-4'
        assert args[0].api_key.get_secret_value() == 'new-api-key'
        assert args[0].base_url is None

        # Verify settings were saved
        settings_store.store.assert_called_once()
        args, kwargs = settings_store.store.call_args
        settings = args[0]
        assert settings.llm_model == 'openai/gpt-4'
        assert settings.llm_api_key.get_secret_value() == 'new-api-key'
        assert settings.llm_base_url is None

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.get_supported_llm_models')
    @patch('openhands.core.cli_settings.organize_models_and_providers')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    async def test_modify_llm_settings_basic_user_cancels(
        self,
        mock_confirm,
        mock_session,
        mock_organize,
        mock_get_models,
        app_config,
        settings_store,
    ):
        # Setup mocks
        mock_get_models.return_value = ['openai/gpt-4', 'anthropic/claude-3-opus']
        mock_organize.return_value = {
            'openai': {'models': ['gpt-4', 'gpt-3.5-turbo'], 'separator': '/'}
        }

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(side_effect=UserCancelledError())
        mock_session.return_value = session_instance

        # Call the function
        await modify_llm_settings_basic(app_config, settings_store)

        # Verify settings were not changed
        app_config.set_llm_config.assert_not_called()
        settings_store.store.assert_not_called()

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.get_supported_llm_models')
    @patch('openhands.core.cli_settings.organize_models_and_providers')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch('openhands.core.cli_settings.print_formatted_text')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    async def test_modify_llm_settings_basic_invalid_input(
        self,
        mock_print,
        mock_confirm,
        mock_session,
        mock_organize,
        mock_get_models,
        app_config,
        settings_store,
    ):
        # Setup mocks
        mock_get_models.return_value = ['openai/gpt-4', 'anthropic/claude-3-opus']
        mock_organize.return_value = {
            'openai': {'models': ['gpt-4', 'gpt-3.5-turbo'], 'separator': '/'}
        }

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(
            side_effect=[
                'invalid-provider',  # First invalid provider
                'openai',  # Valid provider
                'invalid-model',  # Invalid model
                'gpt-4',  # Valid model
                'new-api-key',  # API key
            ]
        )
        mock_session.return_value = session_instance

        # Mock user confirmation to save settings
        mock_confirm.return_value = 0  # "Yes, proceed"

        # Call the function
        await modify_llm_settings_basic(app_config, settings_store)

        # Verify error messages were shown for invalid inputs
        assert (
            mock_print.call_count >= 2
        )  # At least two error messages should be printed

        # Check for invalid provider error
        provider_error_found = False
        model_error_found = False

        for call in mock_print.call_args_list:
            args, _ = call
            if args and isinstance(args[0], HTML):
                if 'Invalid provider selected' in args[0].value:
                    provider_error_found = True
                if 'Invalid model selected' in args[0].value:
                    model_error_found = True

        assert provider_error_found, 'No error message for invalid provider'
        assert model_error_found, 'No error message for invalid model'

        # Verify LLM config was updated with correct values
        app_config.set_llm_config.assert_called_once()

        # Verify settings were saved
        settings_store.store.assert_called_once()
        args, kwargs = settings_store.store.call_args
        settings = args[0]
        assert settings.llm_model == 'openai/gpt-4'
        assert settings.llm_api_key.get_secret_value() == 'new-api-key'
        assert settings.llm_base_url is None


class TestModifyLLMSettingsAdvanced:
    @pytest.fixture
    def app_config(self):
        config = MagicMock(spec=AppConfig)
        llm_config = MagicMock()
        llm_config.model = 'custom-model'
        llm_config.api_key = SecretStr('test-api-key')
        llm_config.base_url = 'https://custom-api.com'
        config.get_llm_config.return_value = llm_config
        config.set_llm_config = MagicMock()
        config.set_agent_config = MagicMock()

        agent_config = MagicMock()
        config.get_agent_config.return_value = agent_config

        # Set up security as a separate mock
        security_mock = MagicMock()
        security_mock.confirmation_mode = True
        config.security = security_mock

        return config

    @pytest.fixture
    def settings_store(self):
        store = MagicMock(spec=FileSettingsStore)
        store.load = AsyncMock(return_value=Settings())
        store.store = AsyncMock()
        return store

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.Agent.list_agents')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.core.cli_settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
    async def test_modify_llm_settings_advanced_success(
        self, mock_confirm, mock_session, mock_list_agents, app_config, settings_store
    ):
        # Setup mocks
        mock_list_agents.return_value = ['default', 'test-agent']

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(
            side_effect=[
                'new-model',  # Custom model
                'https://new-url',  # Base URL
                'new-api-key',  # API key
                'default',  # Agent
            ]
        )
        mock_session.return_value = session_instance

        # Mock user confirmations
        mock_confirm.side_effect = [
            0,  # Enable confirmation mode
            0,  # Enable memory condensation
            0,  # Save settings
        ]

        # Call the function
        await modify_llm_settings_advanced(app_config, settings_store)

        # Verify LLM config was updated
        app_config.set_llm_config.assert_called_once()
        args, kwargs = app_config.set_llm_config.call_args
        assert args[0].model == 'new-model'
        assert args[0].api_key.get_secret_value() == 'new-api-key'
        assert args[0].base_url == 'https://new-url'

        # Verify settings were saved
        settings_store.store.assert_called_once()
        args, kwargs = settings_store.store.call_args
        settings = args[0]
        assert settings.llm_model == 'new-model'
        assert settings.llm_api_key.get_secret_value() == 'new-api-key'
        assert settings.llm_base_url == 'https://new-url'
        assert settings.agent == 'default'
        assert settings.confirmation_mode is True
        assert settings.enable_default_condenser is True

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.Agent.list_agents')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.core.cli_settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
    async def test_modify_llm_settings_advanced_user_cancels(
        self, mock_confirm, mock_session, mock_list_agents, app_config, settings_store
    ):
        # Setup mocks
        mock_list_agents.return_value = ['default', 'test-agent']

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(side_effect=UserCancelledError())
        mock_session.return_value = session_instance

        # Call the function
        await modify_llm_settings_advanced(app_config, settings_store)

        # Verify settings were not changed
        app_config.set_llm_config.assert_not_called()
        settings_store.store.assert_not_called()

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.Agent.list_agents')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch('openhands.core.cli_settings.print_formatted_text')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.core.cli_settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
    async def test_modify_llm_settings_advanced_invalid_agent(
        self,
        mock_print,
        mock_confirm,
        mock_session,
        mock_list_agents,
        app_config,
        settings_store,
    ):
        # Setup mocks
        mock_list_agents.return_value = ['default', 'test-agent']

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(
            side_effect=[
                'new-model',  # Custom model
                'https://new-url',  # Base URL
                'new-api-key',  # API key
                'invalid-agent',  # Invalid agent
                'default',  # Valid agent on retry
            ]
        )
        mock_session.return_value = session_instance

        # Call the function
        await modify_llm_settings_advanced(app_config, settings_store)

        # Verify error message was shown
        assert (
            mock_print.call_count == 3
        )  # Called 3 times: empty line, error message, empty line
        error_message_call = mock_print.call_args_list[
            1
        ]  # The second call contains the error message
        args, kwargs = error_message_call
        assert isinstance(args[0], HTML)
        assert 'Invalid agent' in args[0].value

        # Verify settings were not changed
        app_config.set_llm_config.assert_not_called()
        settings_store.store.assert_not_called()

    @pytest.mark.asyncio
    @patch('openhands.core.cli_settings.Agent.list_agents')
    @patch('openhands.core.cli_settings.PromptSession')
    @patch('openhands.core.cli_settings.cli_confirm')
    @patch(
        'openhands.core.cli_settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.core.cli_settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
    async def test_modify_llm_settings_advanced_user_rejects_save(
        self, mock_confirm, mock_session, mock_list_agents, app_config, settings_store
    ):
        # Setup mocks
        mock_list_agents.return_value = ['default', 'test-agent']

        session_instance = MagicMock()
        session_instance.prompt_async = AsyncMock(
            side_effect=[
                'new-model',  # Custom model
                'https://new-url',  # Base URL
                'new-api-key',  # API key
                'default',  # Agent
            ]
        )
        mock_session.return_value = session_instance

        # Mock user confirmations
        mock_confirm.side_effect = [
            0,  # Enable confirmation mode
            0,  # Enable memory condensation
            1,  # Reject saving settings
        ]

        # Call the function
        await modify_llm_settings_advanced(app_config, settings_store)

        # Verify settings were not changed
        app_config.set_llm_config.assert_not_called()
        settings_store.store.assert_not_called()
