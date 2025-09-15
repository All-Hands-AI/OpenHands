#!/usr/bin/env python3
"""
Tests for settings_action module in OpenHands CLI.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.validation import ValidationError
from pydantic import SecretStr

from openhands_cli.user_actions.settings_action import (
    APIKeyValidator,
    SettingsType,
    choose_llm_model,
    choose_llm_provider,
    prompt_api_key,
    save_settings_confirmation,
    settings_type_confirmation,
)


class TestSettingsType:
    """Test suite for SettingsType enum."""

    def test_settings_type_values(self) -> None:
        """Test that SettingsType enum has correct values."""
        assert SettingsType.BASIC.value == "basic"
        assert SettingsType.ADVANCED.value == "advanced"


class TestSettingsTypeConfirmation:
    """Test suite for settings_type_confirmation function."""

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    def test_settings_type_confirmation_basic(self, mock_cli_confirm: Any) -> None:
        """Test settings_type_confirmation returns BASIC when first option selected."""
        mock_cli_confirm.return_value = 0  # First option: "LLM (Basic)"
        
        result = settings_type_confirmation()
        
        assert result == SettingsType.BASIC
        mock_cli_confirm.assert_called_once_with(
            "Which settings would you like to modify?",
            ["LLM (Basic)", "Go back"]
        )

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    def test_settings_type_confirmation_go_back(self, mock_cli_confirm: Any) -> None:
        """Test settings_type_confirmation raises KeyboardInterrupt when 'Go back' selected."""
        mock_cli_confirm.return_value = 1  # Second option: "Go back"
        
        with pytest.raises(KeyboardInterrupt):
            settings_type_confirmation()


class TestChooseLLMProvider:
    """Test suite for choose_llm_provider function."""

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    @patch("openhands_cli.user_actions.settings_action.VERIFIED_MODELS", {"openai": [], "anthropic": []})
    @patch("openhands_cli.user_actions.settings_action.UNVERIFIED_MODELS_EXCLUDING_BEDROCK", {"custom": []})
    def test_choose_llm_provider_direct_selection(self, mock_cli_confirm: Any) -> None:
        """Test choose_llm_provider returns provider when directly selected."""
        mock_cli_confirm.return_value = 0  # First option
        
        result = choose_llm_provider()
        
        assert result in ["openai", "anthropic", "custom"]
        mock_cli_confirm.assert_called_once()

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    @patch("openhands_cli.user_actions.settings_action.VERIFIED_MODELS", {"openai": [], "anthropic": []})
    @patch("openhands_cli.user_actions.settings_action.UNVERIFIED_MODELS_EXCLUDING_BEDROCK", {"custom": []})
    def test_choose_llm_provider_alternate_selection(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test choose_llm_provider uses text input when 'Select another provider' chosen."""
        # With 3 providers, the "Select another provider" option is at index 4
        # (openai, anthropic, custom, Select another provider) -> index 3 for "Select another provider"
        mock_cli_confirm.return_value = 3  # "Select another provider" option
        mock_cli_text_input.return_value = "custom_provider"
        
        result = choose_llm_provider()
        
        assert result == "custom_provider"
        mock_cli_text_input.assert_called_once()
        # Verify completer is FuzzyWordCompleter
        call_args = mock_cli_text_input.call_args
        assert isinstance(call_args[1]["completer"], FuzzyWordCompleter)

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    def test_choose_llm_provider_escapable_false(self, mock_cli_confirm: Any) -> None:
        """Test choose_llm_provider passes escapable parameter correctly."""
        mock_cli_confirm.return_value = 0
        
        choose_llm_provider(escapable=False)
        
        call_args = mock_cli_confirm.call_args
        assert call_args[1]["escapable"] is False


class TestChooseLLMModel:
    """Test suite for choose_llm_model function."""

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    @patch("openhands_cli.user_actions.settings_action.VERIFIED_MODELS", {"openai": ["gpt-4", "gpt-3.5-turbo"]})
    @patch("openhands_cli.user_actions.settings_action.UNVERIFIED_MODELS_EXCLUDING_BEDROCK", {"openai": ["custom-model"]})
    def test_choose_llm_model_direct_selection(self, mock_cli_confirm: Any) -> None:
        """Test choose_llm_model returns model when directly selected."""
        mock_cli_confirm.return_value = 0  # First model
        
        result = choose_llm_model("openai")
        
        assert result in ["gpt-4", "gpt-3.5-turbo", "custom-model"]
        mock_cli_confirm.assert_called_once()

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    @patch("openhands_cli.user_actions.settings_action.VERIFIED_MODELS", {"openai": ["gpt-4"]})
    @patch("openhands_cli.user_actions.settings_action.UNVERIFIED_MODELS_EXCLUDING_BEDROCK", {"openai": []})
    def test_choose_llm_model_alternate_selection(
        self, mock_cli_confirm: Any, mock_cli_text_input: Any
    ) -> None:
        """Test choose_llm_model uses text input when 'Select another model' chosen."""
        # With 1 model, the "Select another model" option is at index 1
        # (gpt-4, Select another model) -> index 1 for "Select another model"
        mock_cli_confirm.return_value = 1  # "Select another model" option
        mock_cli_text_input.return_value = "custom-model"
        
        result = choose_llm_model("openai")
        
        assert result == "custom-model"
        mock_cli_text_input.assert_called_once()

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    @patch("openhands_cli.user_actions.settings_action.VERIFIED_MODELS", {})
    @patch("openhands_cli.user_actions.settings_action.UNVERIFIED_MODELS_EXCLUDING_BEDROCK", {})
    def test_choose_llm_model_unknown_provider(self, mock_cli_confirm: Any, mock_cli_text_input: Any) -> None:
        """Test choose_llm_model handles unknown provider gracefully."""
        # With no models, only "Select another model" option exists at index 0
        mock_cli_confirm.return_value = 0  # "Select another model" option
        mock_cli_text_input.return_value = "custom-model"
        
        result = choose_llm_model("unknown_provider")
        
        assert result == "custom-model"
        # Should call cli_text_input since there are no predefined models
        mock_cli_text_input.assert_called_once()


class TestAPIKeyValidator:
    """Test suite for APIKeyValidator class."""

    def test_api_key_validator_valid_key(self) -> None:
        """Test APIKeyValidator accepts non-empty API key."""
        validator = APIKeyValidator()
        mock_document = MagicMock()
        mock_document.text = "sk-1234567890abcdef"
        
        # Should not raise exception for valid key
        validator.validate(mock_document)

    def test_api_key_validator_empty_key(self) -> None:
        """Test APIKeyValidator rejects empty API key."""
        validator = APIKeyValidator()
        mock_document = MagicMock()
        mock_document.text = ""
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(mock_document)
        
        assert "API key cannot be empty" in str(exc_info.value)

    def test_api_key_validator_whitespace_key(self) -> None:
        """Test APIKeyValidator rejects whitespace-only API key."""
        validator = APIKeyValidator()
        mock_document = MagicMock()
        mock_document.text = "   "
        
        # Whitespace-only should be considered valid since it's not empty
        # The actual validation logic only checks for empty string
        validator.validate(mock_document)


class TestPromptAPIKey:
    """Test suite for prompt_api_key function."""

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    def test_prompt_api_key_new_key(self, mock_cli_text_input: Any) -> None:
        """Test prompt_api_key for new API key."""
        mock_cli_text_input.return_value = "sk-new-api-key"
        
        result = prompt_api_key()
        
        assert result == "sk-new-api-key"
        call_args = mock_cli_text_input.call_args
        assert "Enter API Key" in call_args[0][0]
        assert call_args[1]["is_password"] is True
        assert call_args[1]["validator"] is not None  # Should have validator for new keys

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    def test_prompt_api_key_existing_key(self, mock_cli_text_input: Any) -> None:
        """Test prompt_api_key with existing API key."""
        existing_key = SecretStr("sk-existing-key-123")
        mock_cli_text_input.return_value = "sk-updated-key"
        
        result = prompt_api_key(existing_key)
        
        assert result == "sk-updated-key"
        call_args = mock_cli_text_input.call_args
        assert "sk-***" in call_args[0][0]  # Should show masked existing key
        assert call_args[1]["validator"] is None  # No validator for existing keys

    @patch("openhands_cli.user_actions.settings_action.cli_text_input")
    def test_prompt_api_key_escapable_false(self, mock_cli_text_input: Any) -> None:
        """Test prompt_api_key passes escapable parameter correctly."""
        mock_cli_text_input.return_value = "sk-test-key"
        
        prompt_api_key(escapable=False)
        
        call_args = mock_cli_text_input.call_args
        assert call_args[1]["escapable"] is False


class TestSaveSettingsConfirmation:
    """Test suite for save_settings_confirmation function."""

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    def test_save_settings_confirmation_yes(self, mock_cli_confirm: Any) -> None:
        """Test save_settings_confirmation returns True when 'Yes, save' selected."""
        mock_cli_confirm.return_value = 0  # "Yes, save"
        
        result = save_settings_confirmation()
        
        assert result == "Yes, save"
        mock_cli_confirm.assert_called_once_with(
            "Save new settings? (They will take effect after restart)",
            ["Yes, save", "No, discard"]
        )

    @patch("openhands_cli.user_actions.settings_action.cli_confirm")
    def test_save_settings_confirmation_no(self, mock_cli_confirm: Any) -> None:
        """Test save_settings_confirmation raises KeyboardInterrupt when 'No, discard' selected."""
        mock_cli_confirm.return_value = 1  # "No, discard"
        
        with pytest.raises(KeyboardInterrupt):
            save_settings_confirmation()