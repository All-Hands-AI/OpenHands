import pytest

from openhands.core.config.mcp_config import MCPConfig


def test_valid_mcp_config():
    """Test a valid MCP configuration."""
    data = {
        'oraichain': {
            'url': 'http://server1:8080'
        }
    }
    result = MCPConfig.from_toml_section(data)
    assert 'oraichain' in result
    assert result['oraichain'].url == 'http://server1:8080'
    assert result['oraichain'].name == 'oraichain'


def test_empty_mcp_config():
    """Test MCP configuration with no servers."""
    data = {}
    result = MCPConfig.from_toml_section(data)
    assert len(result) == 0


def test_invalid_mcp_config():
    """Test MCP configuration with missing required fields."""
    data = {
        'oraichain': {
            # No URL or commands provided
        }
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'MCP oraichain is configured as stdio but no commands are provided' in str(exc_info.value)


def test_multiple_mcp_configs():
    """Test multiple MCP configurations."""
    data = {
        'oraichain': {
            'url': 'http://server1:8080'
        },
        'anthropic': {
            'url': 'http://server2:8080'
        }
    }
    result = MCPConfig.from_toml_section(data)
    assert len(result) == 2
    assert result['oraichain'].url == 'http://server1:8080'
    assert result['anthropic'].url == 'http://server2:8080'
