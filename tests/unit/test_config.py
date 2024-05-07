import os
import tempfile

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
    # Set up
    os.environ['WORKSPACE_BASE'] = '/repos/opendevin/workspace'
    os.environ['LLM_API_KEY'] = 'sk-proj-rgMV0...'
    os.environ['LLM_MODEL'] = 'gpt-3.5-turbo'
    os.environ['AGENT_MEMORY_MAX_THREADS'] = '4'
    os.environ['AGENT_MEMORY_ENABLED'] = 'True'
    os.environ['AGENT'] = 'CodeActAgent'

    # old-style and new-style files
    with open('old_style_config.toml', 'w') as f:
        f.write('[default]\nLLM_MODEL="GPT-4"\n')

    with open('new_style_config.toml', 'w') as f:
        f.write('[app]\nLLM_MODEL="GPT-3"\n')

    with open('.env', 'w') as f:
        f.write('LLM_MODEL=GPT-5\n')

    yield
    # Tear down

    # clean up environment variables
    os.environ.pop('WORKSPACE_BASE', None)
    os.environ.pop('LLM_API_KEY', None)
    os.environ.pop('LLM_MODEL', None)
    os.environ.pop('AGENT_MEMORY_MAX_THREADS', None)
    os.environ.pop('AGENT_MEMORY_ENABLED', None)
    os.environ.pop('AGENT', None)

    # clean up files
    os.remove('old_style_config.toml')
    os.remove('new_style_config.toml')
    os.remove('.env')


def test_compat_env_to_config(setup_env):
    config = AppConfig()
    load_from_env(config, os.environ)
    assert config.workspace_base == '/repos/opendevin/workspace'
    assert isinstance(config.llm, LLMConfig)
    assert config.llm.api_key == 'sk-proj-rgMV0...'
    assert config.llm.model == 'gpt-3.5-turbo'
    assert isinstance(config.agent, AgentConfig)
    assert config.agent.memory_max_threads == 4
    assert isinstance(config.agent.memory_max_threads, int)


@pytest.fixture
def temp_toml_file():
    # Fixture to create a temporary directory and TOML file for testing.
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_toml_file = os.path.join(tmp_dir.name, 'config.toml')
    yield tmp_toml_file
    tmp_dir.cleanup()


@pytest.fixture
def default_config():
    # Fixture to provide a default AppConfig instance.
    yield AppConfig()

    # finalizer


def test_load_from_old_style_env(default_config):
    # Test loading configuration from old-style environment variables.
    os.environ['LLM_API_KEY'] = 'test-api-key'
    os.environ['AGENT_MEMORY_ENABLED'] = 'True'
    os.environ['AGENT_NAME'] = 'PlannerAgent'
    os.environ['workspace_base'] = '/opt/files/workspace'

    load_from_env(default_config, os.environ)

    assert default_config.llm.api_key == 'test-api-key'
    assert default_config.agent.memory_enabled is True
    assert default_config.agent.name == 'PlannerAgent'
    assert default_config.workspace_base == '/opt/files/workspace'


def test_load_from_new_style_toml(default_config, temp_toml_file):
    # Test loading configuration from a new-style TOML file.
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

[agent]
name = "TestAgent"
memory_enabled = true

workspace_base = "/opt/files2/workspace"
""")

    load_from_toml(default_config, temp_toml_file)

    assert default_config.llm.model == 'test-model'
    assert default_config.llm.api_key == 'toml-api-key'
    assert default_config.agent.name == 'TestAgent'
    assert default_config.agent.memory_enabled is True
    assert default_config.workspace_base == '/opt/files2/workspace'


def test_env_overrides_toml(default_config, temp_toml_file):
    # Test that environment variables override TOML values.
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write("""
[llm]
model = "test-model"
api_key = "toml-api-key"

workspace_base = "/opt/files3/workspace"
sandbox_type = "local"
disable_color = True
""")

    os.environ['LLM_API_KEY'] = 'env-api-key'
    os.environ['workspace_base'] = '/opt/files4/workspace'
    os.environ['sandbox_type'] = 'ssh'

    load_from_toml(default_config, temp_toml_file)
    load_from_env(default_config, os.environ)

    assert default_config.llm.model == 'test-model'
    assert default_config.llm.api_key == 'env-api-key'
    assert default_config.workspace_base == '/opt/files4/workspace'
    assert default_config.sandbox_type == 'ssh'
    assert default_config.disable_color is True


def test_defaults_dict_after_updates(default_config):
    """Test that `defaults_dict` retains initial values after updates."""
    initial_defaults = default_config.defaults_dict
    updated_config = AppConfig()
    updated_config.llm.api_key = 'updated-api-key'
    updated_config.agent.name = 'MonologueAgent'

    defaults_after_updates = updated_config.defaults_dict
    assert defaults_after_updates['llm']['api_key']['default'] is None
    assert defaults_after_updates['agent']['name']['default'] == 'CodeActAgent'
    assert defaults_after_updates == initial_defaults


def test_invalid_toml_format(temp_toml_file, default_config):
    # invalid TOML format doesn't break the configuration.
    os.environ['LLM_MODEL'] = 'gpt-5-turbo-1106'
    with open(temp_toml_file, 'w', encoding='utf-8') as toml_file:
        toml_file.write('INVALID TOML CONTENT')

    load_from_toml(default_config)
    load_from_env(default_config)
    assert default_config.llm.model == 'gpt-5-turbo-1106'
    assert default_config.llm.api_key is None


def test_finalize_config(default_config):
    """Test finalize config"""
    default_config.sandbox_type = 'local'
    finalize_config(default_config)

    assert (
        default_config.workspace_mount_path_in_sandbox
        == default_config.workspace_mount_path
    )
