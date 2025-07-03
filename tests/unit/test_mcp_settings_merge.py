"""Test MCP settings merging functionality."""

from unittest.mock import patch

import pytest

from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)
from openhands.server.user_auth.default_user_auth import DefaultUserAuth
from openhands.storage.data_models.settings import Settings


@pytest.mark.asyncio
async def test_mcp_settings_merge_config_only():
    """Test merging when only config.toml has MCP settings."""
    # Mock config.toml with MCP settings
    mock_config_settings = Settings(
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://config-server.com')]
        )
    )

    # Frontend settings without MCP config
    frontend_settings = Settings(llm_model='gpt-4')

    user_auth = DefaultUserAuth()

    with patch.object(Settings, 'from_config', return_value=mock_config_settings):
        merged_settings = user_auth._merge_with_config_settings(frontend_settings)

    # Should use config.toml MCP settings
    assert merged_settings.mcp_config is not None
    assert len(merged_settings.mcp_config.sse_servers) == 1
    assert merged_settings.mcp_config.sse_servers[0].url == 'http://config-server.com'
    assert merged_settings.llm_model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_frontend_only():
    """Test merging when only frontend has MCP settings."""
    # Mock config.toml without MCP settings
    mock_config_settings = Settings(llm_model='claude-3')

    # Frontend settings with MCP config
    frontend_settings = Settings(
        llm_model='gpt-4',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://frontend-server.com')]
        ),
    )

    user_auth = DefaultUserAuth()

    with patch.object(Settings, 'from_config', return_value=mock_config_settings):
        merged_settings = user_auth._merge_with_config_settings(frontend_settings)

    # Should keep frontend MCP settings
    assert merged_settings.mcp_config is not None
    assert len(merged_settings.mcp_config.sse_servers) == 1
    assert merged_settings.mcp_config.sse_servers[0].url == 'http://frontend-server.com'
    assert merged_settings.llm_model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_both_present():
    """Test merging when both config.toml and frontend have MCP settings."""
    # Mock config.toml with MCP settings
    mock_config_settings = Settings(
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://config-server.com')],
            stdio_servers=[
                MCPStdioServerConfig(
                    name='config-stdio', command='config-cmd', args=['arg1']
                )
            ],
        )
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

    user_auth = DefaultUserAuth()

    with patch.object(Settings, 'from_config', return_value=mock_config_settings):
        merged_settings = user_auth._merge_with_config_settings(frontend_settings)

    # Should merge both with config.toml taking priority (appearing first)
    assert merged_settings.mcp_config is not None
    assert len(merged_settings.mcp_config.sse_servers) == 2
    assert merged_settings.mcp_config.sse_servers[0].url == 'http://config-server.com'
    assert merged_settings.mcp_config.sse_servers[1].url == 'http://frontend-server.com'

    assert len(merged_settings.mcp_config.stdio_servers) == 2
    assert merged_settings.mcp_config.stdio_servers[0].name == 'config-stdio'
    assert merged_settings.mcp_config.stdio_servers[1].name == 'frontend-stdio'

    assert merged_settings.llm_model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_no_config():
    """Test merging when config.toml has no MCP settings."""
    # Mock config.toml without MCP settings
    mock_config_settings = None

    # Frontend settings with MCP config
    frontend_settings = Settings(
        llm_model='gpt-4',
        mcp_config=MCPConfig(
            sse_servers=[MCPSSEServerConfig(url='http://frontend-server.com')]
        ),
    )

    user_auth = DefaultUserAuth()

    with patch.object(Settings, 'from_config', return_value=mock_config_settings):
        merged_settings = user_auth._merge_with_config_settings(frontend_settings)

    # Should keep frontend settings unchanged
    assert merged_settings.mcp_config is not None
    assert len(merged_settings.mcp_config.sse_servers) == 1
    assert merged_settings.mcp_config.sse_servers[0].url == 'http://frontend-server.com'
    assert merged_settings.llm_model == 'gpt-4'


@pytest.mark.asyncio
async def test_mcp_settings_merge_neither_present():
    """Test merging when neither config.toml nor frontend have MCP settings."""
    # Mock config.toml without MCP settings
    mock_config_settings = Settings(llm_model='claude-3')

    # Frontend settings without MCP config
    frontend_settings = Settings(llm_model='gpt-4')

    user_auth = DefaultUserAuth()

    with patch.object(Settings, 'from_config', return_value=mock_config_settings):
        merged_settings = user_auth._merge_with_config_settings(frontend_settings)

    # Should keep frontend settings unchanged
    assert merged_settings.mcp_config is None
    assert merged_settings.llm_model == 'gpt-4'
