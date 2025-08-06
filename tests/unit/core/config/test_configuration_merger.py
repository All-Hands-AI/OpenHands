"""Tests for the ConfigurationMerger class."""

from pydantic import SecretStr

from openhands.core.config import OpenHandsConfig
from openhands.core.config.configuration_merger import ConfigurationMerger
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.storage.data_models.settings import Settings


def test_merge_core_settings():
    """Test merging core settings."""
    # Create a config with default values
    config = OpenHandsConfig()

    # Create settings with different values
    settings = Settings(
        agent='TestAgent',
        max_iterations=100,
        max_budget_per_task=50.0,
        git_user_name='test-user',
        git_user_email='test@example.com',
        search_api_key=SecretStr('test-search-key'),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the values from settings
    assert merged_config.default_agent == 'TestAgent'
    assert merged_config.max_iterations == 100
    assert merged_config.max_budget_per_task == 50.0
    assert merged_config.git_user_name == 'test-user'
    assert merged_config.git_user_email == 'test@example.com'
    assert merged_config.search_api_key.get_secret_value() == 'test-search-key'

    # Check that the original config is unchanged
    assert config.default_agent != 'TestAgent'
    assert config.max_iterations != 100
    assert config.max_budget_per_task != 50.0
    assert config.git_user_name != 'test-user'
    assert config.git_user_email != 'test@example.com'
    assert config.search_api_key != SecretStr('test-search-key')


def test_merge_llm_settings():
    """Test merging LLM settings."""
    # Create a config with default values
    config = OpenHandsConfig()

    # Create settings with different values
    settings = Settings(
        llm_model='test-model',
        llm_api_key=SecretStr('test-api-key'),
        llm_base_url='https://test-api.example.com',
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the values from settings
    llm_config = merged_config.get_llm_config()
    assert llm_config.model == 'test-model'
    assert llm_config.api_key.get_secret_value() == 'test-api-key'
    assert llm_config.base_url == 'https://test-api.example.com'

    # Check that the original config is unchanged
    original_llm_config = config.get_llm_config()
    assert original_llm_config.model != 'test-model'
    assert original_llm_config.api_key != SecretStr('test-api-key')
    assert original_llm_config.base_url != 'https://test-api.example.com'


def test_merge_security_settings():
    """Test merging security settings."""
    # Create a config with default values
    config = OpenHandsConfig()

    # Create settings with different values
    settings = Settings(
        confirmation_mode=True,
        security_analyzer='test-analyzer',
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the values from settings
    assert merged_config.security.confirmation_mode is True
    assert merged_config.security.security_analyzer == 'test-analyzer'

    # Check that the original config is unchanged
    assert config.security.confirmation_mode is not True
    assert config.security.security_analyzer != 'test-analyzer'


def test_merge_sandbox_settings():
    """Test merging sandbox settings."""
    # Create a config with default values
    config = OpenHandsConfig()

    # Create settings with different values
    settings = Settings(
        sandbox_base_container_image='test-base-image',
        sandbox_runtime_container_image='test-runtime-image',
        sandbox_api_key=SecretStr('test-sandbox-key'),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the values from settings
    assert merged_config.sandbox.base_container_image == 'test-base-image'
    assert merged_config.sandbox.runtime_container_image == 'test-runtime-image'
    assert merged_config.sandbox.api_key == 'test-sandbox-key'

    # Check that the original config is unchanged
    assert config.sandbox.base_container_image != 'test-base-image'
    assert config.sandbox.runtime_container_image != 'test-runtime-image'
    assert config.sandbox.api_key != 'test-sandbox-key'


def test_merge_mcp_settings_config_only():
    """Test merging MCP settings when only config has MCP settings."""
    # Create a config with MCP settings
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')],
        stdio_servers=[],
        shttp_servers=[],
    )

    # Create settings without MCP config
    settings = Settings(llm_model='test-model')

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the MCP settings from config
    assert len(merged_config.mcp.sse_servers) == 1
    assert merged_config.mcp.sse_servers[0].url == 'http://config-server.com'

    # Check that other settings are applied
    assert merged_config.get_llm_config().model == 'test-model'


def test_merge_mcp_settings_settings_only():
    """Test merging MCP settings when only settings has MCP settings."""
    # Create a config without MCP settings
    config = OpenHandsConfig()
    config.mcp = None

    # Create settings with MCP config
    settings = Settings(
        llm_model='test-model',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://settings-server.com')],
            stdio_servers=[],
            shttp_servers=[],
        ),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the MCP settings from settings
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 1
    assert merged_config.mcp.sse_servers[0].url == 'http://settings-server.com'

    # Check that other settings are applied
    assert merged_config.get_llm_config().model == 'test-model'


def test_merge_mcp_settings_both():
    """Test merging MCP settings when both config and settings have MCP settings."""
    # Create a config with MCP settings
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')],
        stdio_servers=[
            MCPStdioServerConfig(
                name='config-stdio', command='config-cmd', args=['arg1']
            )
        ],
        shttp_servers=[],
    )

    # Create settings with MCP config
    settings = Settings(
        llm_model='test-model',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://settings-server.com')],
            stdio_servers=[
                MCPStdioServerConfig(
                    name='settings-stdio', command='settings-cmd', args=['arg2']
                )
            ],
            shttp_servers=[],
        ),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that the merged config has the MCP settings from both config and settings
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 2
    assert merged_config.mcp.sse_servers[0].url == 'http://config-server.com'
    assert merged_config.mcp.sse_servers[1].url == 'http://settings-server.com'

    assert len(merged_config.mcp.stdio_servers) == 2
    assert merged_config.mcp.stdio_servers[0].name == 'config-stdio'
    assert merged_config.mcp.stdio_servers[1].name == 'settings-stdio'

    # Check that other settings are applied
    assert merged_config.get_llm_config().model == 'test-model'


def test_merge_with_none_values():
    """Test merging with None values in settings."""
    # Create a config with default values
    config = OpenHandsConfig()
    config.default_agent = 'DefaultAgent'
    config.max_iterations = 200

    # Create settings with some None values
    settings = Settings(
        agent=None,  # Should not override
        max_iterations=100,  # Should override
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(settings, config)

    # Check that None values in settings don't override config values
    assert merged_config.default_agent == 'DefaultAgent'

    # Check that non-None values in settings do override config values
    assert merged_config.max_iterations == 100


def test_config_to_settings():
    """Test converting config to settings."""
    # Create a config with custom values
    config = OpenHandsConfig()
    config.default_agent = 'TestAgent'
    config.max_iterations = 100
    config.max_budget_per_task = 50.0
    config.git_user_name = 'test-user'
    config.git_user_email = 'test@example.com'
    config.search_api_key = 'test-search-key'

    # Set LLM config
    llm_config = config.get_llm_config()
    llm_config.model = 'test-model'
    llm_config.api_key = 'test-api-key'
    llm_config.base_url = 'https://test-api.example.com'

    # Set security config
    config.security.confirmation_mode = True
    config.security.security_analyzer = 'test-analyzer'

    # Set sandbox config
    config.sandbox.base_container_image = 'test-base-image'
    config.sandbox.runtime_container_image = 'test-runtime-image'
    config.sandbox.api_key = 'test-sandbox-key'

    # Set MCP config
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')],
        stdio_servers=[
            MCPStdioServerConfig(
                name='config-stdio', command='config-cmd', args=['arg1']
            )
        ],
        shttp_servers=[],
    )

    # Convert config to settings
    settings = ConfigurationMerger.config_to_settings(config)

    # Check that settings has the values from config
    assert settings.agent == 'TestAgent'
    assert settings.max_iterations == 100
    assert settings.max_budget_per_task == 50.0
    assert settings.git_user_name == 'test-user'
    assert settings.git_user_email == 'test@example.com'
    assert settings.search_api_key.get_secret_value() == 'test-search-key'

    assert settings.llm_model == 'test-model'
    assert settings.llm_api_key.get_secret_value() == 'test-api-key'
    assert settings.llm_base_url == 'https://test-api.example.com'

    assert settings.confirmation_mode is True
    assert settings.security_analyzer == 'test-analyzer'

    assert settings.sandbox_base_container_image == 'test-base-image'
    assert settings.sandbox_runtime_container_image == 'test-runtime-image'
    assert settings.sandbox_api_key.get_secret_value() == 'test-sandbox-key'

    assert settings.mcp_config is not None
    assert len(settings.mcp_config.sse_servers) == 1
    assert settings.mcp_config.sse_servers[0].url == 'http://config-server.com'
    assert len(settings.mcp_config.stdio_servers) == 1
    assert settings.mcp_config.stdio_servers[0].name == 'config-stdio'


def test_bidirectional_conversion():
    """Test that config -> settings -> config preserves values."""
    # Create a config with custom values
    original_config = OpenHandsConfig()
    original_config.default_agent = 'TestAgent'
    original_config.max_iterations = 100

    # Set LLM config
    llm_config = original_config.get_llm_config()
    llm_config.model = 'test-model'
    llm_config.api_key = 'test-api-key'

    # Convert config to settings
    settings = ConfigurationMerger.config_to_settings(original_config)

    # Convert settings back to config
    config = ConfigurationMerger.merge_settings_with_config(settings, OpenHandsConfig())

    # Check that the values are preserved
    assert config.default_agent == 'TestAgent'
    assert config.max_iterations == 100
    assert config.get_llm_config().model == 'test-model'
    assert config.get_llm_config().api_key.get_secret_value() == 'test-api-key'
