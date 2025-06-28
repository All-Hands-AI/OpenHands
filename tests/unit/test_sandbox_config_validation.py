"""Tests for sandbox configuration validation."""

import pytest

from openhands.core.config.sandbox_config import SandboxConfig


def test_valid_container_reuse_strategies():
    """Test that valid container reuse strategies are accepted."""
    valid_strategies = ['none', 'pause', 'keep_alive']

    for strategy in valid_strategies:
        config = SandboxConfig(container_reuse_strategy=strategy)
        assert config.container_reuse_strategy == strategy


def test_invalid_container_reuse_strategy():
    """Test that invalid container reuse strategies are rejected."""
    invalid_strategies = ['invalid', 'stop', 'restart', '', 'PAUSE', 'None']

    for strategy in invalid_strategies:
        with pytest.raises(ValueError) as exc_info:
            SandboxConfig(container_reuse_strategy=strategy)

        assert 'Invalid container_reuse_strategy' in str(exc_info.value)
        assert strategy in str(exc_info.value)
        assert 'Must be one of: keep_alive, none, pause' in str(exc_info.value)


def test_default_container_reuse_strategy():
    """Test that the default container reuse strategy is 'none'."""
    config = SandboxConfig()
    assert config.container_reuse_strategy == 'none'


def test_container_reuse_strategy_case_sensitive():
    """Test that container reuse strategy validation is case sensitive."""
    case_variants = ['PAUSE', 'Pause', 'NONE', 'None', 'KEEP_ALIVE', 'Keep_Alive']

    for variant in case_variants:
        with pytest.raises(ValueError) as exc_info:
            SandboxConfig(container_reuse_strategy=variant)

        assert 'Invalid container_reuse_strategy' in str(exc_info.value)


def test_sandbox_config_from_toml_section_valid():
    """Test creating SandboxConfig from TOML data with valid container_reuse_strategy."""
    toml_data = {
        'container_reuse_strategy': 'keep_alive',
        'timeout': 120,
        'user_id': 1000,
    }

    result = SandboxConfig.from_toml_section(toml_data)
    assert 'sandbox' in result
    assert result['sandbox'].container_reuse_strategy == 'keep_alive'


def test_sandbox_config_from_toml_section_invalid():
    """Test creating SandboxConfig from TOML data with invalid container_reuse_strategy."""
    toml_data = {
        'container_reuse_strategy': 'invalid_strategy',
        'timeout': 120,
        'user_id': 1000,
    }

    with pytest.raises(ValueError) as exc_info:
        SandboxConfig.from_toml_section(toml_data)

    assert 'Invalid sandbox configuration' in str(exc_info.value)


def test_other_config_fields_still_work():
    """Test that other configuration fields still work normally."""
    config = SandboxConfig(
        container_reuse_strategy='none',
        timeout=300,
        user_id=1001,
        base_container_image='custom:latest',
        enable_auto_lint=True,
    )

    assert config.container_reuse_strategy == 'none'
    assert config.timeout == 300
    assert config.user_id == 1001
    assert config.base_container_image == 'custom:latest'
    assert config.enable_auto_lint is True
