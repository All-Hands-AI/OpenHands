"""Tests for editor configuration options."""

from openhands.core.config import AgentConfig


def test_editor_config_defaults():
    """Test the default values for editor configuration."""
    config = AgentConfig()

    # Legacy setting
    assert config.enable_editor is True

    # Individual editor settings
    assert config.enable_llm_editor is False
    assert config.enable_claude_editor is False
    assert config.enable_gemini_editor is False


def test_editor_config_override():
    """Test overriding editor configuration values."""
    # Test disabling all editors
    config = AgentConfig(enable_editor=False)
    assert config.enable_editor is False

    # Test enabling LLM editor
    config = AgentConfig(enable_llm_editor=True)
    assert config.enable_llm_editor is True

    # Test enabling Gemini editor
    config = AgentConfig(enable_gemini_editor=True)
    assert config.enable_gemini_editor is True

    # Test disabling Claude editor
    config = AgentConfig(enable_claude_editor=False)
    assert config.enable_claude_editor is False

    # Test enabling all editors
    config = AgentConfig(
        enable_editor=True,
        enable_llm_editor=True,
        enable_claude_editor=True,
        enable_gemini_editor=True,
    )
    assert config.enable_editor is True
    assert config.enable_llm_editor is True
    assert config.enable_claude_editor is True
    assert config.enable_gemini_editor is True
