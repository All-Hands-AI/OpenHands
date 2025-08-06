"""Test MCP settings merging functionality."""

import pytest

from openhands.core.config import ConfigurationMerger, OpenHandsConfig
from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.storage.data_models.settings import Settings


@pytest.mark.asyncio
async def test_mcp_settings_merge_config_only():
    """Test merging when only config.toml has MCP settings."""
    # Create a config with MCP settings
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')]
    )

    # Frontend settings without MCP config
    frontend_settings = Settings(llm_model='gpt-4')

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(
        frontend_settings, config
    )

    # Should use config.toml MCP settings
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 1
    assert merged_config.mcp.sse_servers[0].url == 'http://config-server.com'
    assert merged_config.get_llm_config().model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_frontend_only():
    """Test merging when only frontend has MCP settings."""
    # Create a config without MCP settings
    config = OpenHandsConfig()
    config.mcp = None

    # Set a different LLM model in config
    llm_config = config.get_llm_config()
    llm_config.model = 'claude-3'

    # Frontend settings with MCP config
    frontend_settings = Settings(
        llm_model='gpt-4',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://frontend-server.com')]
        ),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(
        frontend_settings, config
    )

    # Should keep frontend MCP settings
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 1
    assert merged_config.mcp.sse_servers[0].url == 'http://frontend-server.com'
    assert merged_config.get_llm_config().model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_both_present():
    """Test merging when both config.toml and frontend have MCP settings."""
    # Create a config with MCP settings
    config = OpenHandsConfig()
    config.mcp = MCPConfig(
        sse_servers=[MCPSSEServerConfig(url='http://config-server.com')],
        stdio_servers=[
            MCPStdioServerConfig(
                name='config-stdio', command='config-cmd', args=['arg1']
            )
        ],
    )

    # Frontend settings with different MCP config
    frontend_settings = Settings(
        llm_model='gpt-4',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://frontend-server.com')],
            stdio_servers=[
                MCPStdioServerConfig(
                    name='frontend-stdio', command='frontend-cmd', args=['arg2']
                )
            ],
        ),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(
        frontend_settings, config
    )

    # Should merge both with config.toml taking priority (appearing first)
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 2
    assert merged_config.mcp.sse_servers[0].url == 'http://config-server.com'
    assert merged_config.mcp.sse_servers[1].url == 'http://frontend-server.com'

    assert len(merged_config.mcp.stdio_servers) == 2
    assert merged_config.mcp.stdio_servers[0].name == 'config-stdio'
    assert merged_config.mcp.stdio_servers[1].name == 'frontend-stdio'

    assert merged_config.get_llm_config().model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_no_config():
    """Test merging when config has no MCP settings."""
    # Create a config without MCP settings
    config = OpenHandsConfig()
    config.mcp = None

    # Frontend settings with MCP config
    frontend_settings = Settings(
        llm_model='gpt-4',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://frontend-server.com')]
        ),
    )

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(
        frontend_settings, config
    )

    # Should keep frontend settings unchanged
    assert merged_config.mcp is not None
    assert len(merged_config.mcp.sse_servers) == 1
    assert merged_config.mcp.sse_servers[0].url == 'http://frontend-server.com'
    assert merged_config.get_llm_config().model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_neither_present():
    """Test merging when neither config nor frontend have MCP settings."""
    # Create a config without MCP settings
    config = OpenHandsConfig()
    config.mcp = None

    # Set a different LLM model in config
    llm_config = config.get_llm_config()
    llm_config.model = 'claude-3'

    # Frontend settings without MCP config
    frontend_settings = Settings(llm_model='gpt-4')

    # Merge settings with config
    merged_config = ConfigurationMerger.merge_settings_with_config(
        frontend_settings, config
    )

    # Should keep frontend settings unchanged
    assert merged_config.mcp is None
    assert merged_config.get_llm_config().model == 'gpt-4'
