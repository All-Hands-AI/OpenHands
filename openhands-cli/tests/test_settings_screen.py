#!/usr/bin/env python3
"""
Tests for SettingsScreen class in OpenHands CLI.
"""

import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from openhands.sdk import Conversation, LLM
from pydantic import SecretStr

from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.user_actions.settings_action import SettingsType


class TestSettingsScreen:
    """Test suite for SettingsScreen class."""

    def test_settings_screen_init_with_conversation(self) -> None:
        """Test SettingsScreen initialization with conversation."""
        mock_conversation = MagicMock(spec=Conversation)
        settings_screen = SettingsScreen(mock_conversation)
        
        assert settings_screen.conversation == mock_conversation

    def test_settings_screen_init_without_conversation(self) -> None:
        """Test SettingsScreen initialization without conversation."""
        settings_screen = SettingsScreen()
        
        assert settings_screen.conversation is None

    def test_display_settings_no_conversation(self) -> None:
        """Test display_settings returns early when no conversation."""
        settings_screen = SettingsScreen()
        
        # Should return early without error
        settings_screen.display_settings()

    @patch("openhands_cli.tui.settings.settings_screen.print_container")
    @patch.object(SettingsScreen, "configure_settings")
    def test_display_settings_basic_llm(
        self, mock_configure_settings: Any, mock_print_container: Any
    ) -> None:
        """Test display_settings with basic LLM configuration."""
        # Create mock LLM and conversation
        mock_llm = MagicMock(spec=LLM)
        mock_llm.model = "openai/gpt-4"
        mock_llm.api_key = SecretStr("sk-test-key")
        mock_llm.base_url = None  # Basic configuration
        
        mock_agent = MagicMock()
        mock_agent.llm = mock_llm
        
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.agent = mock_agent
        
        settings_screen = SettingsScreen(mock_conversation)
        
        # Call display_settings
        settings_screen.display_settings()
        
        # Verify print_container was called
        mock_print_container.assert_called_once()
        
        # Verify configure_settings was called
        mock_configure_settings.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.print_container")
    @patch.object(SettingsScreen, "configure_settings")
    def test_display_settings_advanced_llm(
        self, mock_configure_settings: Any, mock_print_container: Any
    ) -> None:
        """Test display_settings with advanced LLM configuration."""
        # Create mock LLM with base_url (advanced configuration)
        mock_llm = MagicMock(spec=LLM)
        mock_llm.model = "custom-model"
        mock_llm.api_key = SecretStr("sk-test-key")
        mock_llm.base_url = "https://custom-api.example.com"
        
        mock_agent = MagicMock()
        mock_agent.llm = mock_llm
        
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.agent = mock_agent
        
        settings_screen = SettingsScreen(mock_conversation)
        
        # Call display_settings
        settings_screen.display_settings()
        
        # Verify print_container was called
        mock_print_container.assert_called_once()
        
        # Verify configure_settings was called
        mock_configure_settings.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.print_container")
    @patch.object(SettingsScreen, "configure_settings")
    def test_display_settings_no_api_key(
        self, mock_configure_settings: Any, mock_print_container: Any
    ) -> None:
        """Test display_settings when no API key is set."""
        # Create mock LLM without API key
        mock_llm = MagicMock(spec=LLM)
        mock_llm.model = "openai/gpt-4"
        mock_llm.api_key = None
        mock_llm.base_url = None
        
        mock_agent = MagicMock()
        mock_agent.llm = mock_llm
        
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.agent = mock_agent
        
        settings_screen = SettingsScreen(mock_conversation)
        
        # Call display_settings
        settings_screen.display_settings()
        
        # Verify print_container was called
        mock_print_container.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation")
    @patch.object(SettingsScreen, "handle_basic_settings")
    def test_configure_settings_basic(
        self, mock_handle_basic_settings: Any, mock_settings_type_confirmation: Any
    ) -> None:
        """Test configure_settings with basic settings type."""
        mock_settings_type_confirmation.return_value = SettingsType.BASIC
        
        settings_screen = SettingsScreen()
        settings_screen.configure_settings()
        
        mock_settings_type_confirmation.assert_called_once()
        mock_handle_basic_settings.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation")
    def test_configure_settings_keyboard_interrupt(
        self, mock_settings_type_confirmation: Any
    ) -> None:
        """Test configure_settings handles KeyboardInterrupt."""
        mock_settings_type_confirmation.side_effect = KeyboardInterrupt()
        
        settings_screen = SettingsScreen()
        
        # Should not raise exception
        settings_screen.configure_settings()
        
        mock_settings_type_confirmation.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider")
    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_model")
    @patch("openhands_cli.tui.settings.settings_screen.prompt_api_key")
    @patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation")
    @patch.object(SettingsScreen, "_save_llm_settings")
    def test_handle_basic_settings_success(
        self,
        mock_save_llm_settings: Any,
        mock_save_settings_confirmation: Any,
        mock_prompt_api_key: Any,
        mock_choose_llm_model: Any,
        mock_choose_llm_provider: Any,
    ) -> None:
        """Test handle_basic_settings successful flow."""
        # Setup mocks
        mock_choose_llm_provider.return_value = "openai"
        mock_choose_llm_model.return_value = "gpt-4"
        mock_prompt_api_key.return_value = "sk-test-key"
        mock_save_settings_confirmation.return_value = True
        
        # Create settings screen with conversation
        mock_llm = MagicMock(spec=LLM)
        mock_llm.api_key = SecretStr("sk-existing-key")
        mock_agent = MagicMock()
        mock_agent.llm = mock_llm
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.agent = mock_agent
        
        settings_screen = SettingsScreen(mock_conversation)
        
        # Call handle_basic_settings
        settings_screen.handle_basic_settings()
        
        # Verify all steps were called
        mock_choose_llm_provider.assert_called_once_with(escapable=True)
        mock_choose_llm_model.assert_called_once_with("openai", escapable=True)
        mock_prompt_api_key.assert_called_once_with(mock_llm.api_key, escapable=True)
        mock_save_settings_confirmation.assert_called_once()
        mock_save_llm_settings.assert_called_once_with("openai", "gpt-4", "sk-test-key")

    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider")
    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_model")
    @patch("openhands_cli.tui.settings.settings_screen.prompt_api_key")
    @patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation")
    @patch.object(SettingsScreen, "_save_llm_settings")
    def test_handle_basic_settings_no_conversation(
        self,
        mock_save_llm_settings: Any,
        mock_save_settings_confirmation: Any,
        mock_prompt_api_key: Any,
        mock_choose_llm_model: Any,
        mock_choose_llm_provider: Any,
    ) -> None:
        """Test handle_basic_settings without conversation."""
        # Setup mocks
        mock_choose_llm_provider.return_value = "openai"
        mock_choose_llm_model.return_value = "gpt-4"
        mock_prompt_api_key.return_value = "sk-test-key"
        mock_save_settings_confirmation.return_value = True
        
        settings_screen = SettingsScreen()  # No conversation
        
        # Call handle_basic_settings
        settings_screen.handle_basic_settings()
        
        # Verify prompt_api_key was called with None for existing key
        mock_prompt_api_key.assert_called_once_with(None, escapable=True)
        mock_save_llm_settings.assert_called_once_with("openai", "gpt-4", "sk-test-key")

    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider")
    @patch("openhands_cli.tui.settings.settings_screen.print_formatted_text")
    def test_handle_basic_settings_keyboard_interrupt(
        self, mock_print_formatted_text: Any, mock_choose_llm_provider: Any
    ) -> None:
        """Test handle_basic_settings handles KeyboardInterrupt."""
        mock_choose_llm_provider.side_effect = KeyboardInterrupt()
        
        settings_screen = SettingsScreen()
        
        # Should not raise exception
        settings_screen.handle_basic_settings()
        
        # Verify cancellation message was printed
        mock_print_formatted_text.assert_called_once()

    @patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider")
    def test_handle_basic_settings_escapable_false(
        self, mock_choose_llm_provider: Any
    ) -> None:
        """Test handle_basic_settings with escapable=False."""
        mock_choose_llm_provider.side_effect = KeyboardInterrupt()  # To exit early
        
        settings_screen = SettingsScreen()
        settings_screen.handle_basic_settings(escapable=False)
        
        # Verify escapable=False was passed
        mock_choose_llm_provider.assert_called_once_with(escapable=False)

    @patch("openhands_cli.tui.settings.settings_screen.LLM")
    def test_save_llm_settings(self, mock_llm_class: Any) -> None:
        """Test _save_llm_settings creates and saves LLM configuration."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        
        with patch("openhands_cli.tui.settings.settings_screen.LLM_SETTINGS_PATH", "/tmp/test_llm_settings.json"):
            settings_screen = SettingsScreen()
            
            # Call _save_llm_settings
            settings_screen._save_llm_settings("openai", "gpt-4", "sk-test-key")
            
            # Verify LLM was created with correct parameters
            mock_llm_class.assert_called_once_with(
                model="openai/gpt-4",
                api_key=SecretStr("sk-test-key")
            )
            
            # Verify store_to_json was called
            mock_llm_instance.store_to_json.assert_called_once_with("/tmp/test_llm_settings.json")

    def test_save_llm_settings_integration(self) -> None:
        """Test _save_llm_settings integration with temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        with patch("openhands_cli.tui.settings.settings_screen.LLM_SETTINGS_PATH", temp_path):
            settings_screen = SettingsScreen()
            
            # This should work without raising exceptions
            # Note: We can't easily test the actual file writing without mocking LLM.store_to_json
            # since it depends on the LLM implementation
            with patch("openhands_cli.tui.settings.settings_screen.LLM") as mock_llm_class:
                mock_llm_instance = MagicMock()
                mock_llm_class.return_value = mock_llm_instance
                
                settings_screen._save_llm_settings("openai", "gpt-4", "sk-test-key")
                mock_llm_instance.store_to_json.assert_called_once_with(temp_path)
        
        # Clean up
        import os
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass