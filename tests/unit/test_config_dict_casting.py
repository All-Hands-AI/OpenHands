import os

import pytest

from openhands.core.config import OpenHandsConfig, load_from_env


def test_load_from_env_with_dict(monkeypatch, default_config):
    """Test loading dict values from environment variables, particularly DOCKER_RUNTIME_KWARGS."""
    # Set the environment variable with a dict-formatted string using Python literal syntax
    monkeypatch.setenv(
        'SANDBOX_DOCKER_RUNTIME_KWARGS',
        '{'
        + '  "mem_limit": "2g",'
        + '  "cpu_count": 2,'
        + '  "environment": {"TEST_VAR": "test_value"}'
        + '}',
    )

    # Load configuration from environment
    load_from_env(default_config, os.environ)

    # Verify that the dict was correctly parsed
    assert isinstance(default_config.sandbox.docker_runtime_kwargs, dict)
    assert default_config.sandbox.docker_runtime_kwargs.get('mem_limit') == '2g'
    assert default_config.sandbox.docker_runtime_kwargs.get('cpu_count') == 2
    assert isinstance(
        default_config.sandbox.docker_runtime_kwargs.get('environment'), dict
    )
    assert (
        default_config.sandbox.docker_runtime_kwargs.get('environment').get('TEST_VAR')
        == 'test_value'
    )


@pytest.fixture
def default_config():
    # Fixture to provide a default OpenHandsConfig instance
    yield OpenHandsConfig()
