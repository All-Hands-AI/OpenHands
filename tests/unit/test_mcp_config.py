import pytest

from openhands.core.config.mcp_config import MCPConfig


def test_valid_sse_config():
    """Test a valid SSE configuration."""
    config = MCPConfig(mcp_servers=['http://server1:8080', 'http://server2:8080'])
    config.validate_servers()  # Should not raise any exception


def test_empty_sse_config():
    """Test SSE configuration with empty servers list."""
    config = MCPConfig(mcp_servers=[])
    config.validate_servers()


def test_invalid_sse_url():
    """Test SSE configuration with invalid URL format."""
    config = MCPConfig(mcp_servers=['not_a_url'])
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Invalid URL' in str(exc_info.value)


def test_duplicate_sse_urls():
    """Test SSE configuration with duplicate server URLs."""
    config = MCPConfig(mcp_servers=['http://server1:8080', 'http://server1:8080'])
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Duplicate MCP server URLs are not allowed' in str(exc_info.value)


def test_from_toml_section_valid():
    """Test creating config from valid TOML section."""
    data = {
        'mcp_servers': ['http://server1:8080'],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert result['mcp'].mcp_servers == ['http://server1:8080']


def test_from_toml_section_invalid_sse():
    """Test creating config from TOML section with invalid SSE URL."""
    data = {
        'mcp_servers': ['not_a_url'],
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'Invalid URL' in str(exc_info.value)


def test_complex_urls():
    """Test SSE configuration with complex URLs."""
    config = MCPConfig(
        mcp_servers=[
            'https://user:pass@server1:8080/path?query=1',
            'wss://server2:8443/ws',
            'http://subdomain.example.com:9090',
        ]
    )
    config.validate_servers()  # Should not raise any exception
