from unittest.mock import Mock

import pytest

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.message import TextContent
from openhands.events.observation.commands import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation
from openhands.llm.llm import LLM


@pytest.fixture
def agent() -> CodeActAgent:
    agent = CodeActAgent(llm=LLM(LLMConfig()), config=AgentConfig())
    agent.llm = Mock()
    agent.llm.config = Mock()
    agent.llm.config.max_message_chars = 100
    return agent


def test_cmd_output_observation_message(agent: CodeActAgent):
    obs = CmdOutputObservation(
        command='echo hello', content='Command output', command_id=1, exit_code=0
    )

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Command output' in result.content[0].text
    assert 'Command 1 finished with exit code 0' in result.content[0].text


def test_ipython_run_cell_observation_message(agent: CodeActAgent):
    obs = IPythonRunCellObservation(
        code='plt.plot()',
        content='IPython output\n![image](data:image/png;base64,ABC123)',
    )

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'IPython output' in result.content[0].text
    assert (
        '![image](data:image/png;base64, ...) already displayed to user'
        in result.content[0].text
    )
    assert 'ABC123' not in result.content[0].text


def test_agent_delegate_observation_message(agent: CodeActAgent):
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Delegated agent output' in result.content[0].text


def test_error_observation_message(agent: CodeActAgent):
    obs = ErrorObservation('Error message')

    result = agent.get_observation_message(obs)

    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'OBSERVATION:' in result.content[0].text
    assert 'Error message' in result.content[0].text
    assert 'Error occurred in processing last action' in result.content[0].text


def test_unknown_observation_message(agent: CodeActAgent):
    obs = Mock()

    with pytest.raises(ValueError) as excinfo:
        agent.get_observation_message(obs)
        assert 'Unknown observation type:' in str(excinfo.value)
