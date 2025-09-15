#!/usr/bin/env python3
"""
Integration tests for settings workflow in OpenHands CLI.
"""

import json
import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from openhands.sdk import Conversation, LLM
from pydantic import SecretStr

from openhands_cli.setup import setup_agent
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.user_actions.settings_action import SettingsType


class TestSettingsIntegration:
    """Integration test suite for settings workflow."""

    def test_settings_workflow_end_to_end(self) -> None:
        """Test complete settings workflow from UI to persistence."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch("openhands_cli.tui.settings.settings_screen.LLM_SETTINGS_PATH", temp_path):
                # Mock all user interactions at the settings screen level
                with (
                    patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation") as mock_settings_type,
                    patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider") as mock_provider,
                    patch("openhands_cli.tui.settings.settings_screen.choose_llm_model") as mock_model,
                    patch("openhands_cli.tui.settings.settings_screen.prompt_api_key") as mock_api_key,
                    patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation") as mock_save,
                    patch("openhands_cli.tui.settings.settings_screen.print_container"),
                    patch("openhands_cli.tui.settings.settings_screen.LLM") as mock_llm_class,
                ):
                    # Setup mock responses
                    mock_settings_type.return_value = SettingsType.BASIC
                    mock_provider.return_value = "openai"
                    mock_model.return_value = "gpt-4"
                    mock_api_key.return_value = "sk-test-key-123"
                    mock_save.return_value = True
                    
                    mock_llm_instance = MagicMock()
                    mock_llm_class.return_value = mock_llm_instance
                    
                    # Create settings screen and run workflow
                    settings_screen = SettingsScreen()
                    settings_screen.configure_settings()
                    
                    # Verify all steps were called in correct order
                    mock_settings_type.assert_called_once()
                    mock_provider.assert_called_once_with(escapable=True)
                    mock_model.assert_called_once_with("openai", escapable=True)
                    mock_api_key.assert_called_once_with(None, escapable=True)
                    mock_save.assert_called_once()
                    
                    # Verify LLM settings were saved
                    mock_llm_instance.store_to_json.assert_called_once_with(temp_path)
        
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def test_settings_workflow_with_existing_conversation(self) -> None:
        """Test settings workflow when conversation already exists."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch("openhands_cli.tui.settings.settings_screen.LLM_SETTINGS_PATH", temp_path):
                # Create mock conversation with existing LLM
                mock_llm = MagicMock(spec=LLM)
                mock_llm.model = "anthropic/claude-3-sonnet"
                mock_llm.api_key = SecretStr("sk-existing-key")
                mock_llm.base_url = None
                
                mock_agent = MagicMock()
                mock_agent.llm = mock_llm
                
                mock_conversation = MagicMock(spec=Conversation)
                mock_conversation.agent = mock_agent
                
                # Mock user interactions
                with (
                    patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation") as mock_settings_type,
                    patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider") as mock_provider,
                    patch("openhands_cli.tui.settings.settings_screen.choose_llm_model") as mock_model,
                    patch("openhands_cli.tui.settings.settings_screen.prompt_api_key") as mock_api_key,
                    patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation") as mock_save,
                    patch("openhands_cli.tui.settings.settings_screen.print_container"),
                    patch("openhands_cli.tui.settings.settings_screen.LLM") as mock_llm_class,
                ):
                    # Setup mock responses
                    mock_settings_type.return_value = SettingsType.BASIC
                    mock_provider.return_value = "openai"
                    mock_model.return_value = "gpt-4"
                    mock_api_key.return_value = "sk-updated-key"
                    mock_save.return_value = True
                    
                    mock_llm_instance = MagicMock()
                    mock_llm_class.return_value = mock_llm_instance
                    
                    # Create settings screen with existing conversation
                    settings_screen = SettingsScreen(mock_conversation)
                    settings_screen.display_settings()
                    
                    # Verify existing API key was passed to prompt_api_key
                    mock_api_key.assert_called_once_with(mock_llm.api_key, escapable=True)
                    
                    # Verify settings were saved
                    mock_llm_instance.store_to_json.assert_called_once_with(temp_path)
        
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def test_settings_workflow_cancellation_at_different_steps(self) -> None:
        """Test settings workflow cancellation at different steps."""
        # Test cancellation at settings type selection
        with patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation") as mock_settings_type:
            mock_settings_type.side_effect = KeyboardInterrupt()
            
            settings_screen = SettingsScreen()
            settings_screen.configure_settings()  # Should not raise exception
            
            mock_settings_type.assert_called_once()

        # Test cancellation at provider selection
        with (
            patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation") as mock_settings_type,
            patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider") as mock_provider,
            patch("openhands_cli.tui.settings.settings_screen.print_formatted_text") as mock_print,
        ):
            mock_settings_type.return_value = SettingsType.BASIC
            mock_provider.side_effect = KeyboardInterrupt()
            
            settings_screen = SettingsScreen()
            settings_screen.configure_settings()
            
            # Should print cancellation message
            mock_print.assert_called_once()

        # Test cancellation at save confirmation
        with (
            patch("openhands_cli.tui.settings.settings_screen.settings_type_confirmation") as mock_settings_type,
            patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider") as mock_provider,
            patch("openhands_cli.tui.settings.settings_screen.choose_llm_model") as mock_model,
            patch("openhands_cli.tui.settings.settings_screen.prompt_api_key") as mock_api_key,
            patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation") as mock_save,
            patch("openhands_cli.tui.settings.settings_screen.print_formatted_text") as mock_print,
        ):
            mock_settings_type.return_value = SettingsType.BASIC
            mock_provider.return_value = "openai"
            mock_model.return_value = "gpt-4"
            mock_api_key.return_value = "sk-test-key"
            mock_save.side_effect = KeyboardInterrupt()
            
            settings_screen = SettingsScreen()
            settings_screen.configure_settings()
            
            # Should print cancellation message
            mock_print.assert_called_once()

    @patch("openhands_cli.setup.LLM.load_from_json")
    def test_setup_agent_with_saved_settings(self, mock_load_from_json: Any) -> None:
        """Test setup_agent loads settings from saved JSON file."""
        # Mock successful loading from JSON
        mock_llm = MagicMock(spec=LLM)
        mock_llm.model = "openai/gpt-4"
        mock_load_from_json.return_value = mock_llm
        
        with (
            patch("openhands_cli.setup.Agent") as mock_agent_class,
            patch("openhands_cli.setup.Conversation") as mock_conversation_class,
            patch("openhands_cli.setup.BashExecutor"),
            patch("openhands_cli.setup.FileEditorExecutor"),
            patch("openhands_cli.setup.print_formatted_text"),
        ):
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            mock_conversation_instance = MagicMock()
            mock_conversation_class.return_value = mock_conversation_instance
            
            result = setup_agent()
            
            # Verify LLM was loaded from JSON
            mock_load_from_json.assert_called_once()
            
            # Verify agent was created with loaded LLM
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            assert call_args[1]["llm"] == mock_llm
            
            # Verify conversation was created
            assert result == mock_conversation_instance

    @patch("openhands_cli.setup.LLM.load_from_json")
    def test_setup_agent_no_saved_settings(self, mock_load_from_json: Any) -> None:
        """Test setup_agent returns None when no saved settings exist."""
        # Mock FileNotFoundError when loading from JSON
        mock_load_from_json.side_effect = FileNotFoundError()
        
        result = setup_agent()
        
        # Should return None when no settings file exists
        assert result is None
        mock_load_from_json.assert_called_once()

    def test_settings_persistence_file_structure(self) -> None:
        """Test that settings are persisted in the correct file structure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch("openhands_cli.locations.LLM_SETTINGS_PATH", temp_path):
                # Create a real LLM instance and save it
                llm = LLM(model="openai/gpt-4", api_key=SecretStr("sk-test-key"))
                llm.store_to_json(temp_path)
                
                # Verify file was created and contains expected structure
                assert os.path.exists(temp_path)
                
                with open(temp_path, 'r') as f:
                    saved_data = json.load(f)
                
                # Verify basic structure (exact format depends on LLM implementation)
                assert isinstance(saved_data, dict)
                # The exact keys depend on the LLM serialization format
                # but we can verify it's valid JSON
        
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def test_settings_ui_display_formatting(self) -> None:
        """Test that settings UI displays information correctly."""
        # Test basic LLM display
        mock_llm = MagicMock(spec=LLM)
        mock_llm.model = "openai/gpt-4"
        mock_llm.api_key = SecretStr("sk-test-key")
        mock_llm.base_url = None
        
        mock_agent = MagicMock()
        mock_agent.llm = mock_llm
        
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.agent = mock_agent
        
        with (
            patch("openhands_cli.tui.settings.settings_screen.print_container") as mock_print_container,
            patch.object(SettingsScreen, "configure_settings"),
        ):
            settings_screen = SettingsScreen(mock_conversation)
            settings_screen.display_settings()
            
            # Verify print_container was called (UI was displayed)
            mock_print_container.assert_called_once()
            
            # Get the Frame that was passed to print_container
            call_args = mock_print_container.call_args
            frame = call_args[0][0]
            
            # Verify frame has correct title
            assert frame.title == "Settings"

        # Test advanced LLM display
        mock_llm.base_url = "https://custom-api.example.com"
        
        with (
            patch("openhands_cli.tui.settings.settings_screen.print_container") as mock_print_container,
            patch.object(SettingsScreen, "configure_settings"),
        ):
            settings_screen = SettingsScreen(mock_conversation)
            settings_screen.display_settings()
            
            # Verify print_container was called for advanced settings too
            mock_print_container.assert_called_once()

    def test_settings_workflow_non_escapable_mode(self) -> None:
        """Test settings workflow in non-escapable mode."""
        with (
            patch("openhands_cli.tui.settings.settings_screen.choose_llm_provider") as mock_provider,
            patch("openhands_cli.tui.settings.settings_screen.choose_llm_model") as mock_model,
            patch("openhands_cli.tui.settings.settings_screen.prompt_api_key") as mock_api_key,
            patch("openhands_cli.tui.settings.settings_screen.save_settings_confirmation") as mock_save,
            patch("openhands_cli.tui.settings.settings_screen.LLM") as mock_llm_class,
        ):
            # Setup mock responses
            mock_provider.return_value = "openai"
            mock_model.return_value = "gpt-4"
            mock_api_key.return_value = "sk-test-key"
            mock_save.return_value = True
            
            mock_llm_instance = MagicMock()
            mock_llm_class.return_value = mock_llm_instance
            
            settings_screen = SettingsScreen()
            settings_screen.handle_basic_settings(escapable=False)
            
            # Verify all functions were called with escapable=False
            mock_provider.assert_called_once_with(escapable=False)
            mock_model.assert_called_once_with("openai", escapable=False)
            mock_api_key.assert_called_once_with(None, escapable=False)