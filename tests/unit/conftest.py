import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.llm.llm import LLM


@pytest.fixture
def llm_config():
    return LLMConfig(
        model='test_model',
        api_key='test_key',
    )


@pytest.fixture
def agent_config():
    return AgentConfig()


@pytest.fixture
def llm(llm_config):
    return LLM(llm_config)


@pytest.fixture
def codeact_agent(llm, agent_config):
    return CodeActAgent(llm, agent_config)
