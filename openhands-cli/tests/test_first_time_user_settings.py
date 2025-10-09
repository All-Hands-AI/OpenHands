"""Tests for first-time user settings flow improvements."""

import pytest
from unittest.mock import patch, MagicMock

from openhands_cli.agent_chat import _start_fresh_conversation, run_cli_entry
from openhands_cli.setup import MissingAgentSpec
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.user_actions.settings_action import SettingsType, settings_type_confirmation


class TestFirstTimeUserSettingsEscape:
    """Test that first-time users can escape the settings setup flow."""

    def test_first_time_user_can_escape_settings_setup(self):
        """Test that first-time users can escape settings setup and CLI exits gracefully."""
        with (
            patch('openhands_cli.agent_chat.setup_conversation') as mock_setup,
            patch('openhands_cli.agent_chat.print_formatted_text') as mock_print,
            patch.object(SettingsScreen, 'configure_settings') as mock_configure,
        ):
            # First call raises MissingAgentSpec (first-time user)
            # Second call also raises MissingAgentSpec (user escaped settings)
            mock_setup.side_effect = [MissingAgentSpec(), MissingAgentSpec()]
            # User escapes during settings configuration (no exception raised, just returns)
            mock_configure.return_value = None

            # This should raise MissingAgentSpec and be caught by run_cli_entry
            with pytest.raises(MissingAgentSpec):
                _start_fresh_conversation()

            # Verify configure_settings was called with first_time=True
            mock_configure.assert_called_once_with(first_time=True)

    def test_run_cli_entry_handles_escaped_first_time_setup(self):
        """Test that run_cli_entry handles escaped first-time setup gracefully."""
        with (
            patch('openhands_cli.agent_chat._start_fresh_conversation') as mock_start,
            patch('openhands_cli.agent_chat.print_formatted_text') as mock_print,
        ):
            mock_start.side_effect = MissingAgentSpec()

            # Should not raise exception, should print goodbye message
            run_cli_entry()

            # Verify goodbye messages were printed
            assert mock_print.call_count == 2
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert any('Setup is required' in str(call) for call in calls)
            assert any('Goodbye!' in str(call) for call in calls)

    def test_successful_setup_after_first_time_configuration(self):
        """Test that setup succeeds after first-time user completes configuration."""
        mock_conversation = MagicMock()
        
        with (
            patch('openhands_cli.agent_chat.setup_conversation') as mock_setup,
            patch.object(SettingsScreen, 'configure_settings') as mock_configure,
        ):
            # First call raises MissingAgentSpec, second call succeeds
            mock_setup.side_effect = [MissingAgentSpec(), mock_conversation]

            result = _start_fresh_conversation()

            # Verify configure_settings was called with first_time=True
            mock_configure.assert_called_once_with(first_time=True)
            # Verify setup_conversation was called twice
            assert mock_setup.call_count == 2
            # Verify we got the conversation back
            assert result == mock_conversation


class TestFirstTimeUserAdvancedSettings:
    """Test that first-time users can choose advanced settings."""

    @pytest.mark.parametrize("choice_index,expected_type", [
        (0, SettingsType.BASIC),
        (1, SettingsType.ADVANCED),
    ])
    def test_first_time_user_settings_type_choices(self, choice_index, expected_type, mock_cli_interactions):
        """Test that first-time users get basic/advanced choice without 'Go back' option."""
        mock_cli_interactions.cli_confirm.return_value = choice_index

        result = settings_type_confirmation(first_time=True)

        assert result == expected_type
        # Verify the question and choices for first-time users
        call_args = mock_cli_interactions.cli_confirm.call_args
        question, choices = call_args[0]
        
        assert 'Welcome to OpenHands!' in question
        assert 'Choose your preferred setup method:' in question
        assert choices == ['LLM (Basic)', 'LLM (Advanced)']
        assert 'Go back' not in choices

    def test_returning_user_settings_type_choices(self, mock_cli_interactions):
        """Test that returning users get the 'Go back' option."""
        mock_cli_interactions.cli_confirm.return_value = 0

        result = settings_type_confirmation(first_time=False)

        assert result == SettingsType.BASIC
        # Verify the question and choices for returning users
        call_args = mock_cli_interactions.cli_confirm.call_args
        question, choices = call_args[0]
        
        assert 'Which settings would you like to modify?' in question
        assert choices == ['LLM (Basic)', 'LLM (Advanced)', 'Go back']

    def test_returning_user_can_go_back(self, mock_cli_interactions):
        """Test that returning users can select 'Go back' option."""
        mock_cli_interactions.cli_confirm.return_value = 2  # 'Go back' is index 2

        with pytest.raises(KeyboardInterrupt):
            settings_type_confirmation(first_time=False)

    def test_first_time_user_configure_settings_flow(self):
        """Test that configure_settings properly handles first_time parameter."""
        screen = SettingsScreen()
        
        with (
            patch('openhands_cli.tui.settings.settings_screen.settings_type_confirmation') as mock_type,
            patch.object(screen, 'handle_basic_settings') as mock_basic,
            patch.object(screen, 'handle_advanced_settings') as mock_advanced,
        ):
            # Test basic settings flow for first-time user
            mock_type.return_value = SettingsType.BASIC
            screen.configure_settings(first_time=True)
            
            mock_type.assert_called_once_with(first_time=True)
            mock_basic.assert_called_once()
            mock_advanced.assert_not_called()

            # Reset mocks and test advanced settings flow
            mock_type.reset_mock()
            mock_basic.reset_mock()
            mock_advanced.reset_mock()
            
            mock_type.return_value = SettingsType.ADVANCED
            screen.configure_settings(first_time=True)
            
            mock_type.assert_called_once_with(first_time=True)
            mock_advanced.assert_called_once()
            mock_basic.assert_not_called()

    def test_first_time_user_can_escape_during_settings_type_selection(self):
        """Test that first-time users can escape during settings type selection."""
        screen = SettingsScreen()
        
        with patch('openhands_cli.tui.settings.settings_screen.settings_type_confirmation') as mock_type:
            mock_type.side_effect = KeyboardInterrupt()
            
            # Should not raise exception, should return gracefully
            screen.configure_settings(first_time=True)
            
            mock_type.assert_called_once_with(first_time=True)


class TestSettingsWorkflowIntegration:
    """Test integration of the new settings workflow."""

    def test_basic_settings_workflow_maintains_escapability(self):
        """Test that basic settings workflow maintains escapability for all steps."""
        screen = SettingsScreen()
        
        with (
            patch('openhands_cli.tui.settings.settings_screen.choose_llm_provider') as mock_provider,
            patch('openhands_cli.tui.settings.settings_screen.choose_llm_model') as mock_model,
            patch('openhands_cli.tui.settings.settings_screen.prompt_api_key') as mock_api_key,
            patch('openhands_cli.tui.settings.settings_screen.save_settings_confirmation') as mock_save,
        ):
            mock_provider.return_value = 'openai'
            mock_model.return_value = 'gpt-4o-mini'
            mock_api_key.return_value = 'sk-test'
            mock_save.return_value = True

            screen.handle_basic_settings()

            # Verify all functions were called with escapable=True
            mock_provider.assert_called_once()
            provider_call_kwargs = mock_provider.call_args.kwargs
            assert provider_call_kwargs.get('escapable', True) is True

            mock_model.assert_called_once()
            model_call_kwargs = mock_model.call_args.kwargs
            assert model_call_kwargs.get('escapable', True) is True

            mock_api_key.assert_called_once()
            api_key_call_kwargs = mock_api_key.call_args.kwargs
            assert api_key_call_kwargs.get('escapable', True) is True

    def test_keyboard_interrupt_handling_in_basic_settings(self):
        """Test that KeyboardInterrupt is properly handled in basic settings."""
        screen = SettingsScreen()
        
        with (
            patch('openhands_cli.tui.settings.settings_screen.choose_llm_provider') as mock_provider,
            patch.object(screen.agent_store, 'save') as mock_save,
        ):
            mock_provider.side_effect = KeyboardInterrupt()

            # Should not raise exception, should return gracefully
            screen.handle_basic_settings()

            # Verify no settings were saved
            mock_save.assert_not_called()

    @pytest.mark.parametrize("interrupt_step", [
        'provider', 'model', 'api_key', 'save'
    ])
    def test_keyboard_interrupt_at_each_basic_settings_step(self, interrupt_step):
        """Test that KeyboardInterrupt is handled at each step of basic settings."""
        screen = SettingsScreen()
        
        with (
            patch('openhands_cli.tui.settings.settings_screen.choose_llm_provider') as mock_provider,
            patch('openhands_cli.tui.settings.settings_screen.choose_llm_model') as mock_model,
            patch('openhands_cli.tui.settings.settings_screen.prompt_api_key') as mock_api_key,
            patch('openhands_cli.tui.settings.settings_screen.save_settings_confirmation') as mock_save,
            patch.object(screen.agent_store, 'save') as mock_store_save,
        ):
            # Set up happy path defaults
            mock_provider.return_value = 'openai'
            mock_model.return_value = 'gpt-4o-mini'
            mock_api_key.return_value = 'sk-test'
            mock_save.return_value = True

            # Inject KeyboardInterrupt at the specified step
            if interrupt_step == 'provider':
                mock_provider.side_effect = KeyboardInterrupt()
            elif interrupt_step == 'model':
                mock_model.side_effect = KeyboardInterrupt()
            elif interrupt_step == 'api_key':
                mock_api_key.side_effect = KeyboardInterrupt()
            elif interrupt_step == 'save':
                mock_save.side_effect = KeyboardInterrupt()

            # Should not raise exception, should return gracefully
            screen.handle_basic_settings()

            # Verify no settings were saved when interrupted
            mock_store_save.assert_not_called()