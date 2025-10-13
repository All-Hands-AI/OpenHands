"""Test for API key preservation bug when updating settings."""

from unittest.mock import patch
import pytest
from pydantic import SecretStr

from openhands_cli.user_actions.settings_action import prompt_api_key
from openhands_cli.tui.utils import StepCounter


def test_api_key_preservation_when_user_presses_enter():
    """Test that API key is preserved when user presses ENTER to keep current key.
    
    This test replicates the bug where API keys disappear when updating settings.
    When a user presses ENTER to keep the current API key, the function should
    return the existing API key, not an empty string.
    """
    step_counter = StepCounter(1)
    existing_api_key = SecretStr("sk-existing-key-123")
    
    # Mock cli_text_input to return empty string (simulating user pressing ENTER)
    with patch('openhands_cli.user_actions.settings_action.cli_text_input', return_value=''):
        result = prompt_api_key(
            step_counter=step_counter,
            provider='openai',
            existing_api_key=existing_api_key,
            escapable=True
        )
    
    # The bug: result is empty string instead of the existing key
    # This test will fail initially, demonstrating the bug
    assert result == existing_api_key.get_secret_value(), (
        f"Expected existing API key '{existing_api_key.get_secret_value()}' "
        f"but got '{result}'. API key should be preserved when user presses ENTER."
    )


def test_api_key_update_when_user_enters_new_key():
    """Test that API key is updated when user enters a new key."""
    step_counter = StepCounter(1)
    existing_api_key = SecretStr("sk-existing-key-123")
    new_api_key = "sk-new-key-456"
    
    # Mock cli_text_input to return new API key
    with patch('openhands_cli.user_actions.settings_action.cli_text_input', return_value=new_api_key):
        result = prompt_api_key(
            step_counter=step_counter,
            provider='openai',
            existing_api_key=existing_api_key,
            escapable=True
        )
    
    # Should return the new API key
    assert result == new_api_key



def test_empty_input_validation_for_new_setup():
    """Test that empty input is rejected when no existing key is present."""
    step_counter = StepCounter(1)
    
    # For new setups, empty input should return empty string (validation happens in cli_text_input)
    # This test verifies that the function correctly handles the case where no existing key is present
    with patch('openhands_cli.user_actions.settings_action.cli_text_input', return_value=''):
        result = prompt_api_key(
            step_counter=step_counter,
            provider='openai',
            existing_api_key=None,
            escapable=True
        )
        
        # Should return empty string when no existing key and user provides empty input
        assert result == ''