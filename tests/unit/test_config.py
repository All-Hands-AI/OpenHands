import os

import pytest

from opendevin.core.config import (
    AgentConfig,
    AppConfig,
    LLMConfig,
    finalize_config,
    load_from_env,
    load_from_toml,
)


@pytest.fixture
def setup_env():
    # Create old-style and new-style TOML files
    with open('old_style_config.toml', 'w') as f:
        f.write('[default]\nLLM_MODEL="GPT-4"\n')

    with open('new_style_config.toml', 'w') as f:
        f.write('[app]\nLLM_MODEL="GPT-3"\n')

    yield

    # Cleanup TOML files after the test
    os.remove('old_style_config.toml')
    os.remove('new_style_config.toml')


def test_compat_env_to_config(monkeypatch, setup_env):
    # Use `monkeypatch` to set environment variables for this specific test
    monkeypatch.setenv('WORKSPACE_BASE', '/repos/opendevin/workspace')
    monkeypatch.setenv('LLM_API_KEY', 'sk-proj-rgMV0...')
    monkeypatch.setenv('LLM_MODEL', 'gpt-3.5-turbo')
    monkeypatch.setenv('AGENT_MEMORY_MAX_THREADS', '4')
    monkeypatch.setenv('AGENT_MEMORY_ENABLED', 'True')
    monkeypatch.setenv('AGENT', 'CodeActAgent')

    config = AppConfig()
    load_from_env(config, os.environ)

    assert config.workspace_base == '/repos/opendevin/workspace'
    assert isinstance(config.llm, LLMConfig)
    assert config.llm.api_key == 'sk-proj-rgMV0...'
    assert config.llm.model == 'gpt-3.5-turbo'
    assert isinstance(config.agent, AgentConfig)
    assert isinstance(config.agent.memory_max_threads, int)
    assert config.agent.memory_max_threads == 4


@pytest.fixture
def temp_toml_file(tmp_path):
    # Fixture to create a temporary directory and TOML file for testing
    tmp_toml_file = os.path.join(tmp_path, 'config.toml')
    yield tmp_toml_file


@pytest.fixture
def default_config(monkeypatch):
    # Fixture to provide a default AppConfig instance
    AppConfig.reset()
    yield AppConfig()


def test_load_from_old_style_env(monkeypatch, default_config):
    # Test loading configuration from old-style environment variables using monkeypatch
    monkeypatch.setenv('LLM_API_KEY', 'test-api-key')
    monkeypatch.setenv('AGENT_MEMORY_ENABLED', 'True')
    monkeypatch.setenv('AGENT_NAME', 'PlannerAgent')
    monkeypatch.setenv('WORKSPACE_BASE', '/opt/files/workspace')

    load_from_env(default_config, os.environ)

    assert default_config.llm.api_key == 'test-api-key'
    assert default_config.agent.memory_enabled is True
    assert default_config.agent.name == 'PlannerAgent'
    assert default_config.workspace_base == '/opt/files/workspace'


def test_load_from_new_style_toml(default_config, temp_toml_file):
    # Test loading configuration from a new-style TOML file
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

[agent]
name = "TestAgent"
memory_enabled = true

[core]
workspace_base = "/opt/files2/workspace"
""")

    load_from_toml(default_config, temp_toml_file)

    assert default_config.llm.model == 'test-model'
    assert default_config.llm.api_key == 'toml-api-key'
    assert default_config.agent.name == 'TestAgent'
    assert default_config.agent.memory_enabled is True
    assert default_config.workspace_base == '/opt/files2/workspace'


def test_env_overrides_toml(monkeypatch, default_config, temp_toml_file):
    # Test that environment variables override TOML values using monkeypatch
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

[core]
workspace_base = "/opt/files3/workspace"
sandbox_type = "local"
disable_color = true
""")

    monkeypatch.setenv('LLM_API_KEY', 'env-api-key')
    monkeypatch.setenv('WORKSPACE_BASE', '/opt/files4/workspace')
    monkeypatch.setenv('SANDBOX_TYPE', 'ssh')

    load_from_toml(default_config, temp_toml_file)
    load_from_env(default_config, os.environ)

    assert os.environ.get('LLM_MODEL') is None
    assert default_config.llm.model == 'test-model'
    assert default_config.llm.api_key == 'env-api-key'
    assert default_config.workspace_base == '/opt/files4/workspace'
    assert default_config.sandbox_type == 'ssh'
    assert default_config.disable_color is True


def test_defaults_dict_after_updates(default_config):
    # Test that `defaults_dict` retains initial values after updates.
    initial_defaults = default_config.defaults_dict
    updated_config = AppConfig()
    updated_config.llm.api_key = 'updated-api-key'
    updated_config.agent.name = 'MonologueAgent'

    defaults_after_updates = updated_config.defaults_dict
    assert defaults_after_updates['llm']['api_key']['default'] is None
    assert defaults_after_updates['agent']['name']['default'] == 'CodeActAgent'
    assert defaults_after_updates == initial_defaults

    AppConfig.reset()


def test_invalid_toml_format(monkeypatch, temp_toml_file, default_config):
    # Invalid TOML format doesn't break the configuration
    monkeypatch.setenv('LLM_MODEL', 'gpt-5-turbo-1106')
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write('INVALID TOML CONTENT')

    load_from_toml(default_config)
    load_from_env(default_config, os.environ)
    assert default_config.llm.model == 'gpt-5-turbo-1106'
    assert default_config.llm.custom_llm_provider is None
    assert default_config.github_token is None
    assert default_config.llm.api_key is None


def test_finalize_config(default_config):
    # Test finalize config
    default_config.sandbox_type = 'local'
    finalize_config(default_config)

    assert (
        default_config.workspace_mount_path_in_sandbox
        == default_config.workspace_mount_path
    )
