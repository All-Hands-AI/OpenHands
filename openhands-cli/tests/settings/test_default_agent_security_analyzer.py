"""Test that first-time settings screen usage creates a default agent with security analyzer."""

from unittest.mock import patch
import pytest
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.user_actions.settings_action import SettingsType
from openhands.sdk import LLM
from pydantic import SecretStr


def test_first_time_settings_creates_default_agent_with_security_analyzer():
    """Test that using the settings screen for the first time creates a default agent with a non-None security analyzer."""
    
    # Create a settings screen instance (no conversation initially)
    screen = SettingsScreen(conversation=None)
    
    # Mock all the user interaction steps to simulate first-time setup
    with (
        patch(
            'openhands_cli.tui.settings.settings_screen.settings_type_confirmation',
            return_value=SettingsType.BASIC,
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.choose_llm_provider',
            return_value='openai',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.choose_llm_model',
            return_value='gpt-4o-mini',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.prompt_api_key',
            return_value='sk-test-key-123',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.save_settings_confirmation',
            return_value=True,
        ),
    ):
        # Run the settings configuration workflow
        screen.configure_settings(first_time=True)
    
    # Load the saved agent from the store
    saved_agent = screen.agent_store.load()
    
    # Verify that an agent was created and saved
    assert saved_agent is not None, "Agent should be created and saved after first-time settings configuration"
    
    # Verify that the agent has the expected LLM configuration
    assert saved_agent.llm.model == 'openai/gpt-4o-mini', f"Expected model 'openai/gpt-4o-mini', got '{saved_agent.llm.model}'"
    assert saved_agent.llm.api_key.get_secret_value() == 'sk-test-key-123', "API key should match the provided value"
    
    # Verify that the agent has a security analyzer and it's not None
    assert hasattr(saved_agent, 'security_analyzer'), "Agent should have a security_analyzer attribute"
    assert saved_agent.security_analyzer is not None, "Security analyzer should not be None"
    
    # Verify the security analyzer has the expected type/kind
    assert hasattr(saved_agent.security_analyzer, 'kind'), "Security analyzer should have a 'kind' attribute"
    assert saved_agent.security_analyzer.kind == 'LLMSecurityAnalyzer', f"Expected security analyzer kind 'LLMSecurityAnalyzer', got '{saved_agent.security_analyzer.kind}'"


def test_first_time_settings_with_advanced_configuration():
    """Test that advanced settings also create a default agent with security analyzer."""
    
    screen = SettingsScreen(conversation=None)
    
    with (
        patch(
            'openhands_cli.tui.settings.settings_screen.settings_type_confirmation',
            return_value=SettingsType.ADVANCED,
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.prompt_custom_model',
            return_value='anthropic/claude-3-5-sonnet',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.prompt_base_url',
            return_value='https://api.anthropic.com',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.prompt_api_key',
            return_value='sk-ant-test-key',
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.choose_memory_condensation',
            return_value=True,
        ),
        patch(
            'openhands_cli.tui.settings.settings_screen.save_settings_confirmation',
            return_value=True,
        ),
    ):
        screen.configure_settings(first_time=True)
    
    saved_agent = screen.agent_store.load()
    
    # Verify agent creation and security analyzer
    assert saved_agent is not None, "Agent should be created with advanced settings"
    assert saved_agent.security_analyzer is not None, "Security analyzer should not be None in advanced settings"
    assert saved_agent.security_analyzer.kind == 'LLMSecurityAnalyzer', "Security analyzer should be LLMSecurityAnalyzer"
    
    # Verify advanced settings were applied
    assert saved_agent.llm.model == 'anthropic/claude-3-5-sonnet', "Custom model should be set"
    assert saved_agent.llm.base_url == 'https://api.anthropic.com', "Base URL should be set"