import pytest

from openhands.core.config.mcp_config import MCPConfig, MCPSSEConfig, MCPStdioConfig


def test_valid_sse_config():
    """Test a valid SSE configuration."""
    config = MCPSSEConfig(mcp_servers=['http://server1:8080', 'http://server2:8080'])
    config.validate_servers()  # Should not raise any exception


def test_empty_sse_config():
    """Test SSE configuration with empty servers list."""
    config = MCPSSEConfig(mcp_servers=[])
    config.validate_servers()


def test_invalid_sse_url():
    """Test SSE configuration with invalid URL format."""
    config = MCPSSEConfig(mcp_servers=['not_a_url'])
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Invalid URL' in str(exc_info.value)


def test_duplicate_sse_urls():
    """Test SSE configuration with duplicate server URLs."""
    config = MCPSSEConfig(mcp_servers=['http://server1:8080', 'http://server1:8080'])
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Duplicate MCP server URLs are not allowed' in str(exc_info.value)


def test_valid_stdio_config():
    """Test a valid stdio configuration."""
    config = MCPStdioConfig(
        commands=['python', 'python3'], args=[['-m', 'server1'], ['-m', 'server2']]
    )
    config.validate_stdio()  # Should not raise any exception


def test_empty_stdio_config():
    """Test stdio configuration with empty commands list."""
    config = MCPStdioConfig(commands=[], args=[])
    config.validate_stdio()


def test_mismatched_stdio_lengths():
    """Test stdio configuration with mismatched number of commands and args."""
    config = MCPStdioConfig(
        commands=['python', 'python3'],
        args=[['-m', 'server1']],  # Only one args list for two commands
    )
    with pytest.raises(ValueError) as exc_info:
        config.validate_stdio()
    assert 'Number of commands (2) does not match number of args lists (1)' in str(
        exc_info.value
    )


def test_valid_combined_config():
    """Test a valid combined MCP configuration with both SSE and stdio."""
    MCPConfig(
        sse=MCPSSEConfig(mcp_servers=['http://server1:8080']),
        stdio=MCPStdioConfig(commands=['python'], args=[['-m', 'server1']]),
    )
    # Should not raise any exception


def test_from_toml_section_valid():
    """Test creating config from valid TOML section."""
    data = {
        'mcp-sse': {'mcp_servers': ['http://server1:8080']},
        'mcp-stdio': {'commands': ['python'], 'args': [['-m', 'server1']]},
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert result['mcp'].sse.mcp_servers == ['http://server1:8080']
    assert result['mcp'].stdio.commands == ['python']
    assert result['mcp'].stdio.args == [['-m', 'server1']]


def test_from_toml_section_invalid_sse():
    """Test creating config from TOML section with invalid SSE URL."""
    data = {
        'mcp-sse': {'mcp_servers': ['not_a_url']},
        'mcp-stdio': {'commands': ['python'], 'args': [['-m', 'server1']]},
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'Invalid URL' in str(exc_info.value)


def test_from_toml_section_invalid_stdio():
    """Test creating config from TOML section with mismatched stdio config."""
    data = {
        'mcp-sse': {'mcp_servers': ['http://server1:8080']},
        'mcp-stdio': {
            'commands': ['python', 'python3'],
            'args': [['-m', 'server1']],  # Only one args list for two commands
        },
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'Number of commands (2) does not match number of args lists (1)' in str(
        exc_info.value
    )


def test_complex_urls():
    """Test SSE configuration with complex URLs."""
    config = MCPSSEConfig(
        mcp_servers=[
            'https://user:pass@server1:8080/path?query=1',
            'wss://server2:8443/ws',
            'http://subdomain.example.com:9090',
        ]
    )
    config.validate_servers()  # Should not raise any exception
