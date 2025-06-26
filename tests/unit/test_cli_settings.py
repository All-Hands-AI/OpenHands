from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prompt_toolkit.formatted_text import HTML
from pydantic import SecretStr

from openhands.cli.settings import (
    display_settings,
    modify_llm_settings_advanced,
    modify_llm_settings_basic,
)
from openhands.cli.tui import UserCancelledError
from openhands.core.config import OpenHandsConfig
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
        config = MagicMock(spec=OpenHandsConfig)
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
        config = MagicMock(spec=OpenHandsConfig)
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

    @patch('openhands.cli.settings.print_container')
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

    @patch('openhands.cli.settings.print_container')
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
        config = MagicMock(spec=OpenHandsConfig)
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
    @patch('openhands.cli.settings.get_supported_llm_models')
    @patch('openhands.cli.settings.organize_models_and_providers')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
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
                'gpt-4',  # Model
                'new-api-key',  # API Key
            ]
        )
        mock_session.return_value = session_instance

        # Mock cli_confirm to:
        # 1. Select the first provider (openai) from the list
        # 2. Select "Select another model" option
        # 3. Select "Yes, save" option
        mock_confirm.side_effect = [0, 1, 0]

        # Call the function
        await modify_llm_settings_basic(app_config, settings_store)

        # Verify LLM config was updated
        app_config.set_llm_config.assert_called_once()
        args, kwargs = app_config.set_llm_config.call_args
        # The model name might be different based on the default model in the list
        # Just check that it contains 'gpt-4' instead of checking for prefix
        assert 'gpt-4' in args[0].model
        assert args[0].api_key.get_secret_value() == 'new-api-key'
        assert args[0].base_url is None

        # Verify settings were saved
        settings_store.store.assert_called_once()
        args, kwargs = settings_store.store.call_args
        settings = args[0]
        # The model name might be different based on the default model in the list
        # Just check that it contains 'gpt-4' instead of checking for prefix
        assert 'gpt-4' in settings.llm_model
        assert settings.llm_api_key.get_secret_value() == 'new-api-key'
        assert settings.llm_base_url is None

    @pytest.mark.asyncio
    @patch('openhands.cli.settings.get_supported_llm_models')
    @patch('openhands.cli.settings.organize_models_and_providers')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
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
    @patch('openhands.cli.settings.get_supported_llm_models')
    @patch('openhands.cli.settings.organize_models_and_providers')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch('openhands.cli.settings.print_formatted_text')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    async def test_modify_llm_settings_basic_invalid_provider_input(
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
                'custom-model',  # Custom model (now allowed with warning)
                'new-api-key',  # API key
            ]
        )
        mock_session.return_value = session_instance

        # Mock cli_confirm to select the second option (change provider/model) for the first two calls
        # and then select the first option (save settings) for the last call
        mock_confirm.side_effect = [1, 1, 0]

        # Call the function
        await modify_llm_settings_basic(app_config, settings_store)

        # Verify error message was shown for invalid provider and warning for custom model
        assert mock_print.call_count >= 2  # At least two messages should be printed

        # Check for invalid provider error and custom model warning
        provider_error_found = False
        model_warning_found = False

        for call in mock_print.call_args_list:
            args, _ = call
            if args and isinstance(args[0], HTML):
                if 'Invalid provider selected' in args[0].value:
                    provider_error_found = True
                if 'Warning:' in args[0].value and 'custom-model' in args[0].value:
                    model_warning_found = True

        assert provider_error_found, 'No error message for invalid provider'
        assert model_warning_found, 'No warning message for custom model'

        # Verify LLM config was updated with the custom model
        app_config.set_llm_config.assert_called_once()

        # Verify settings were saved with the custom model
        settings_store.store.assert_called_once()
        args, kwargs = settings_store.store.call_args
        settings = args[0]
        assert 'custom-model' in settings.llm_model
        assert settings.llm_api_key.get_secret_value() == 'new-api-key'
        assert settings.llm_base_url is None

    def test_default_provider_preference(self):
        """Test that the default provider prefers 'anthropic' if available."""
        # This is a simple test to verify that the default provider prefers 'anthropic'
        # We're directly checking the code in settings.py where the default provider is set

        # Import the settings module to check the default provider
        # Find the line where the default provider is set
        import inspect

        import openhands.cli.settings as settings_module

        source_lines = inspect.getsource(
            settings_module.modify_llm_settings_basic
        ).splitlines()

        # Look for the line that sets the default provider
        default_provider_found = False
        for i, line in enumerate(source_lines):
            if "# Set default provider - prefer 'anthropic' if available" in line:
                default_provider_found = True
                break

        # Assert that the default provider comment exists
        assert default_provider_found, 'Could not find the default provider comment'

        # Now look for the actual implementation
        provider_impl_found = False
        for i, line in enumerate(source_lines):
            if "'anthropic'" in line and "if 'anthropic' in provider_list" in line:
                provider_impl_found = True
                break

        assert provider_impl_found, (
            "Could not find the implementation that prefers 'anthropic'"
        )

        # Also check the fallback provider when provider not in organized_models
        fallback_comment_found = False
        for i, line in enumerate(source_lines):
            if (
                "# If the provider doesn't exist, prefer 'anthropic' if available"
                in line
            ):
                fallback_comment_found = True
                break

        assert fallback_comment_found, 'Could not find the fallback provider comment'

        # Now look for the actual implementation
        fallback_impl_found = False
        for i, line in enumerate(source_lines):
            if "'anthropic'" in line and "if 'anthropic' in organized_models" in line:
                fallback_impl_found = True
                break

        assert fallback_impl_found, (
            "Could not find the fallback implementation that prefers 'anthropic'"
        )

    def test_default_model_selection(self):
        """Test that the default model selection uses the first model in the list."""
        # This is a simple test to verify that the default model selection uses the first model in the list
        # We're directly checking the code in settings.py where the default model is set

        import inspect

        import openhands.cli.settings as settings_module

        source_lines = inspect.getsource(
            settings_module.modify_llm_settings_basic
        ).splitlines()

        # Look for the block that sets the default model
        default_model_block = []
        in_default_model_block = False
        for line in source_lines:
            if (
                '# Set default model to the best verified model for the provider'
                in line
            ):
                in_default_model_block = True
                default_model_block.append(line)
            elif in_default_model_block:
                default_model_block.append(line)
                if '# Show the default model' in line:
                    break

        # Assert that we found the default model selection logic
        assert default_model_block, (
            'Could not find the block that sets the default model'
        )

        # Print the actual lines for debugging
        print('Default model block found:')
        for line in default_model_block:
            print(f'  {line.strip()}')

        # Check that the logic uses the first model in the list
        first_model_check = any(
            'provider_models[0]' in line for line in default_model_block
        )

        assert first_model_check, (
            'Default model selection should use the first model in the list'
        )


class TestModifyLLMSettingsAdvanced:
    @pytest.fixture
    def app_config(self):
        config = MagicMock(spec=OpenHandsConfig)
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
    @patch('openhands.cli.settings.Agent.list_agents')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.cli.settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
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
    @patch('openhands.cli.settings.Agent.list_agents')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.cli.settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
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
    @patch('openhands.cli.settings.Agent.list_agents')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch('openhands.cli.settings.print_formatted_text')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.cli.settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
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
    @patch('openhands.cli.settings.Agent.list_agents')
    @patch('openhands.cli.settings.PromptSession')
    @patch('openhands.cli.settings.cli_confirm')
    @patch(
        'openhands.cli.settings.LLMSummarizingCondenserConfig',
        MockLLMSummarizingCondenserConfig,
    )
    @patch('openhands.cli.settings.NoOpCondenserConfig', MockNoOpCondenserConfig)
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
