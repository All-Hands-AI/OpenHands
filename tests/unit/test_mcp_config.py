import pytest
from pydantic import ValidationError

from openhands.core.config.mcp_config import (
    MCPConfig,
    MCPSSEServerConfig,
    MCPStdioServerConfig,
)


def test_valid_sse_config():
    """Test a valid SSE configuration."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='http://server1:8080'),
            MCPSSEServerConfig(url='http://server2:8080'),
        ]
    )
    config.validate_servers()  # Should not raise any exception


def test_empty_sse_config():
    """Test SSE configuration with empty servers list."""
    config = MCPConfig(sse_servers=[])
    config.validate_servers()


def test_invalid_sse_url():
    """Test SSE configuration with invalid URL format."""
    config = MCPConfig(sse_servers=[MCPSSEServerConfig(url='not_a_url')])
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Invalid URL' in str(exc_info.value)


def test_duplicate_sse_urls():
    """Test SSE configuration with duplicate server URLs."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='http://server1:8080'),
            MCPSSEServerConfig(url='http://server1:8080'),
        ]
    )
    with pytest.raises(ValueError) as exc_info:
        config.validate_servers()
    assert 'Duplicate MCP server URLs are not allowed' in str(exc_info.value)


def test_from_toml_section_valid():
    """Test creating config from valid TOML section."""
    data = {
        'sse_servers': ['http://server1:8080'],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert len(result['mcp'].sse_servers) == 1
    assert result['mcp'].sse_servers[0].url == 'http://server1:8080'


def test_from_toml_section_invalid_sse():
    """Test creating config from TOML section with invalid SSE URL."""
    data = {
        'sse_servers': ['not_a_url'],
    }
    with pytest.raises(ValueError) as exc_info:
        MCPConfig.from_toml_section(data)
    assert 'Invalid URL' in str(exc_info.value)


def test_complex_urls():
    """Test SSE configuration with complex URLs."""
    config = MCPConfig(
        sse_servers=[
            MCPSSEServerConfig(url='https://user:pass@server1:8080/path?query=1'),
            MCPSSEServerConfig(url='wss://server2:8443/ws'),
            MCPSSEServerConfig(url='http://subdomain.example.com:9090'),
        ]
    )
    config.validate_servers()  # Should not raise any exception


def test_mcp_sse_server_config_with_api_key():
    """Test MCPSSEServerConfig with API key."""
    config = MCPSSEServerConfig(url='http://server1:8080', api_key='test-api-key')
    assert config.url == 'http://server1:8080'
    assert config.api_key == 'test-api-key'


def test_mcp_sse_server_config_without_api_key():
    """Test MCPSSEServerConfig without API key."""
    config = MCPSSEServerConfig(url='http://server1:8080')
    assert config.url == 'http://server1:8080'
    assert config.api_key is None


def test_mcp_stdio_server_config_basic():
    """Test basic MCPStdioServerConfig."""
    config = MCPStdioServerConfig(name='test-server', command='python')
    assert config.name == 'test-server'
    assert config.command == 'python'
    assert config.args == []
    assert config.env == {}


def test_mcp_stdio_server_config_with_args_and_env():
    """Test MCPStdioServerConfig with args and env."""
    config = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true', 'PORT': '8080'},
    )
    assert config.name == 'test-server'
    assert config.command == 'python'
    assert config.args == ['-m', 'server']
    assert config.env == {'DEBUG': 'true', 'PORT': '8080'}


def test_mcp_config_with_stdio_servers():
    """Test MCPConfig with stdio servers."""
    stdio_server = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true'},
    )
    config = MCPConfig(stdio_servers=[stdio_server])
    assert len(config.stdio_servers) == 1
    assert config.stdio_servers[0].name == 'test-server'
    assert config.stdio_servers[0].command == 'python'
    assert config.stdio_servers[0].args == ['-m', 'server']
    assert config.stdio_servers[0].env == {'DEBUG': 'true'}


def test_from_toml_section_with_stdio_servers():
    """Test creating config from TOML section with stdio servers."""
    data = {
        'sse_servers': ['http://server1:8080'],
        'stdio_servers': [
            {
                'name': 'test-server',
                'command': 'python',
                'args': ['-m', 'server'],
                'env': {'DEBUG': 'true'},
            }
        ],
    }
    result = MCPConfig.from_toml_section(data)
    assert 'mcp' in result
    assert len(result['mcp'].sse_servers) == 1
    assert result['mcp'].sse_servers[0].url == 'http://server1:8080'
    assert len(result['mcp'].stdio_servers) == 1
    assert result['mcp'].stdio_servers[0].name == 'test-server'
    assert result['mcp'].stdio_servers[0].command == 'python'
    assert result['mcp'].stdio_servers[0].args == ['-m', 'server']
    assert result['mcp'].stdio_servers[0].env == {'DEBUG': 'true'}


def test_mcp_config_with_both_server_types():
    """Test MCPConfig with both SSE and stdio servers."""
    sse_server = MCPSSEServerConfig(url='http://server1:8080', api_key='test-api-key')
    stdio_server = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['-m', 'server'],
        env={'DEBUG': 'true'},
    )
    config = MCPConfig(sse_servers=[sse_server], stdio_servers=[stdio_server])
    assert len(config.sse_servers) == 1
    assert config.sse_servers[0].url == 'http://server1:8080'
    assert config.sse_servers[0].api_key == 'test-api-key'
    assert len(config.stdio_servers) == 1
    assert config.stdio_servers[0].name == 'test-server'
    assert config.stdio_servers[0].command == 'python'


def test_mcp_config_model_validation_error():
    """Test MCPConfig validation error with invalid data."""
    with pytest.raises(ValidationError):
        # Missing required 'url' field
        MCPSSEServerConfig()

    with pytest.raises(ValidationError):
        # Missing required 'name' and 'command' fields
        MCPStdioServerConfig()


def test_mcp_config_extra_fields_forbidden():
    """Test that extra fields are forbidden in MCPConfig."""
    with pytest.raises(ValidationError):
        MCPConfig(extra_field='value')

    # Note: The nested models don't have 'extra': 'forbid' set, so they allow extra fields
    # We're only testing the main MCPConfig class here


def test_stdio_server_equality_with_different_env_order():
    """Test that MCPStdioServerConfig equality works with env in different order but respects arg order."""
    # Test 1: Same args, different env order
    server1 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    server2 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],  # Same order
        env={'PORT': '8080', 'DEBUG': 'true'},  # Different order
    )

    # Should be equal because env is compared as a set
    assert server1 == server2

    # Test 2: Different args order
    server3 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--debug', '--port=8080', '--verbose'],  # Different order
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    # Should NOT be equal because args order matters
    assert server1 != server3

    # Test 3: Different arg value
    server4 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=9090'],  # Different port
        env={'DEBUG': 'true', 'PORT': '8080'},
    )

    # Should not be equal
    assert server1 != server4

    # Test 4: Different env value
    server5 = MCPStdioServerConfig(
        name='test-server',
        command='python',
        args=['--verbose', '--debug', '--port=8080'],
        env={'DEBUG': 'true', 'PORT': '9090'},  # Different port
    )

    # Should not be equal
    assert server1 != server5


@pytest.mark.unit
def test_mcp_config_default_timeout():
    """Verify that the default_timeout in MCPConfig is initialized to 30.0.

    This test ensures the timeout has a standard fallback value, which is crucial for 
    maintaining default behavior in MCP connections when no overrides are provided.
    It checks the basic initialization to confirm consistency across environments.
    """
    config = MCPConfig()
    assert config.default_timeout == 30.0


@pytest.mark.unit
def test_mcp_config_timeout_override():
    """Test manual overriding of the default_timeout in MCPConfig.

    This verifies that users can specify custom timeout values, allowing for 
    flexibility in scenarios like high-latency networks. It ensures the field 
    accepts and retains overrides correctly.
    """
    config = MCPConfig(default_timeout=60.0)
    assert config.default_timeout == 60.0


@pytest.mark.unit
def test_mcp_config_timeout_with_env_override(monkeypatch):
    """Test overriding default_timeout via environment variables.

    This test simulates real-world configuration scenarios where environment 
    variables take precedence, ensuring the system integrates with external 
    settings. It covers dynamic overrides and validates their application.
    """
    monkeypatch.setenv('MCP_DEFAULT_TIMEOUT', '90.0')
    with patch('openhands.core.config.load_from_env') as mock_load_env:
        mock_load_env.return_value = {'default_timeout': 90.0}
        config = MCPConfig()
        assert config.default_timeout == 90.0


@pytest.mark.unit
def test_mcp_config_invalid_timeout():
    """Test that invalid timeout values (e.g., negative) raise a ValidationError.

    This ensures type and value safety, preventing misconfigurations that could 
    lead to runtime errors. It covers edge cases like negative values to enforce 
    positive timeouts only.
    """
    with pytest.raises(ValidationError):
        MCPConfig(default_timeout=-10.0)


@pytest.mark.unit
def test_mcp_config_zero_timeout():
    """Test that zero timeout values raise a ValidationError.

    Zero timeouts could cause immediate failures in connections, so this test 
    enforces that only positive values are accepted, improving overall reliability.
    """
    with pytest.raises(ValidationError):
        MCPConfig(default_timeout=0.0)


@pytest.mark.unit
def test_mcp_config_non_float_timeout():
    """Test that non-float values for timeout raise a ValidationError.

    This verifies type enforcement, ensuring the field only accepts numeric values 
    to prevent configuration errors in production environments.
    """
    with pytest.raises(ValidationError):
        MCPConfig(default_timeout='not_a_float')
