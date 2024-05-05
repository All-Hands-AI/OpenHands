import os

import pytest

from opendevin.core.config import AgentConfig, AppConfig, LLMConfig, load_from_env


@pytest.fixture
def setup_env():
    # Set up
    os.environ['WORKSPACE_BASE'] = '/Users/enyst/repos/devin/workspace'
    os.environ['LLM_API_KEY'] = 'sk-proj-rgMV0...'
    os.environ['LLM_MODEL'] = 'gpt-3.5-turbo'
    os.environ['AGENT_MEMORY_MAX_THREADS'] = '4'
    os.environ['AGENT_MEMORY_ENABLED'] = 'True'
    os.environ['AGENT'] = 'CodeActAgent'
    yield
    # Tear down
    os.environ.pop('WORKSPACE_BASE', None)
    os.environ.pop('LLM_API_KEY', None)
    os.environ.pop('LLM_MODEL', None)
    os.environ.pop('AGENT_MEMORY_MAX_THREADS', None)
    os.environ.pop('AGENT_MEMORY_ENABLED', None)
    os.environ.pop('AGENT', None)


def test_compat_env_to_config(setup_env):
    config = AppConfig()
    load_from_env(config, os.environ)
    assert config.workspace_base == '/Users/enyst/repos/devin/workspace'
    assert isinstance(config.llm, LLMConfig)
    assert config.llm.api_key == 'sk-proj-rgMV0...'
    assert config.llm.model == 'gpt-3.5-turbo'
    assert isinstance(config.agent, AgentConfig)
    assert config.agent.memory_max_threads == 4
    assert isinstance(config.agent.memory_max_threads, int)  # Check type casting
