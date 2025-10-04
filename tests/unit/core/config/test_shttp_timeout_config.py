"""Test MCP SHTTP server timeout configuration."""

import pytest
from pydantic import ValidationError

from openhands.core.config.mcp_config import MCPSHTTPServerConfig


class TestMCPSHTTPServerConfig:
    """Test SHTTP server configuration with timeout field."""

    def test_shttp_config_with_timeout(self):
        """Test SHTTP config accepts timeout parameter."""
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=90)
        assert config.timeout == 90
        assert config.url == 'https://api.example.com/mcp'
        assert config.api_key is None

    def test_shttp_config_with_api_key_and_timeout(self):
        """Test SHTTP config with both API key and timeout."""
        config = MCPSHTTPServerConfig(
            url='https://api.example.com/mcp', api_key='test-key-123', timeout=120
        )
        assert config.timeout == 120
        assert config.api_key == 'test-key-123'

    def test_shttp_config_default_timeout(self):
        """Test SHTTP config uses default timeout when not specified."""
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp')
        assert config.timeout == 60  # Default value

    def test_shttp_config_none_timeout(self):
        """Test SHTTP config accepts None timeout."""
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=None)
        assert config.timeout is None

    def test_timeout_validation_positive_values(self):
        """Test timeout validation accepts positive values."""
        # Test various valid timeout values
        valid_timeouts = [1, 5, 30, 60, 120, 300, 600, 1800, 3600]

        for timeout in valid_timeouts:
            config = MCPSHTTPServerConfig(
                url='https://api.example.com/mcp', timeout=timeout
            )
            assert config.timeout == timeout

    def test_timeout_validation_zero_raises_error(self):
        """Test timeout validation rejects zero timeout."""
        with pytest.raises(ValidationError) as exc_info:
            MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=0)
        assert 'Timeout must be positive' in str(exc_info.value)

    def test_timeout_validation_negative_raises_error(self):
        """Test timeout validation rejects negative timeout."""
        with pytest.raises(ValidationError) as exc_info:
            MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=-10)
        assert 'Timeout must be positive' in str(exc_info.value)

    def test_timeout_validation_max_limit(self):
        """Test timeout validation enforces maximum limit."""
        # Test exactly at the limit
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=3600)
        assert config.timeout == 3600

        # Test exceeding the limit
        with pytest.raises(ValidationError) as exc_info:
            MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=3601)
        assert 'Timeout cannot exceed 3600 seconds' in str(exc_info.value)

    def test_timeout_validation_way_over_limit(self):
        """Test timeout validation rejects very large values."""
        with pytest.raises(ValidationError) as exc_info:
            MCPSHTTPServerConfig(
                url='https://api.example.com/mcp',
                timeout=86400,  # 24 hours
            )
        assert 'Timeout cannot exceed 3600 seconds' in str(exc_info.value)

    def test_url_validation_still_works(self):
        """Test that existing URL validation still works with timeout field."""
        # Valid URL should work
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=30)
        assert config.url == 'https://api.example.com/mcp'

        # Invalid URL should fail
        with pytest.raises(ValidationError):
            MCPSHTTPServerConfig(url='not-a-url', timeout=30)

    def test_backward_compatibility_no_timeout(self):
        """Test backward compatibility - config works without timeout field."""
        # Should work exactly like before the timeout field was added
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp')
        assert config.url == 'https://api.example.com/mcp'
        assert config.api_key is None
        assert config.timeout == 60  # Default

    def test_model_dump_includes_timeout(self):
        """Test that model serialization includes timeout field."""
        config = MCPSHTTPServerConfig(
            url='https://api.example.com/mcp', api_key='test-key', timeout=90
        )

        data = config.model_dump()
        expected = {
            'url': 'https://api.example.com/mcp',
            'api_key': 'test-key',
            'timeout': 90,
        }
        assert data == expected

    def test_model_dump_with_none_timeout(self):
        """Test model serialization with None timeout."""
        config = MCPSHTTPServerConfig(url='https://api.example.com/mcp', timeout=None)

        data = config.model_dump()
        expected = {
            'url': 'https://api.example.com/mcp',
            'api_key': None,
            'timeout': None,
        }
        assert data == expected
