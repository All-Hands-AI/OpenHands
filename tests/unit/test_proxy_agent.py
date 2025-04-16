from unittest.mock import Mock

import pytest

from openhands.agenthub.proxy_agent.function_calling import (
    DelegateLocalTool,
    DelegateRemoteOHTool,
    FinishTool,
    get_tools,
    response_to_action,
)
from openhands.agenthub.proxy_agent.proxy_agent import ProxyAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.exceptions import FunctionCallNotExistsError
from openhands.core.message import Message, TextContent
from openhands.events.action import (
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import EventSource
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.reject import UserRejectObservation
from openhands.llm.llm import LLM


@pytest.fixture
def agent() -> ProxyAgent:
    config = AgentConfig()
    agent = ProxyAgent(llm=LLM(LLMConfig()), config=config)
    agent.llm = Mock()
    agent.llm.config = Mock()
    agent.llm.config.max_message_chars = 1000
    return agent


@pytest.fixture
def mock_state() -> State:
    state = Mock(spec=State)
    state.history = []
    state.extra_data = {}

    return state


def test_ipython_run_cell_observation_message(agent: ProxyAgent):
    obs = IPythonRunCellObservation(
        code='print("Hello, world!")',
        content='IPython output\nHello, world!\n',
    )

    message = agent._get_observation_message(obs)

    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'system'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)
    assert 'IPython output' in message.content[0].text


def test_agent_delegate_observation_message(agent: ProxyAgent):
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    message = agent._get_observation_message(obs)

    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'system'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)
    assert (
        message.content[0].text
        == 'Content\nOutputs: {"content": "Delegated agent output"}'
    )


def test_error_observation_message(agent: ProxyAgent):
    obs = ErrorObservation('Error message')

    message = agent._get_observation_message(obs)

    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'system'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)
    assert (
        message.content[0].text
        == 'Error message\n[Error occurred in processing last action]'
    )


def test_unknown_observation_message(agent: ProxyAgent):
    obs = Mock()

    with pytest.raises(ValueError, match='Unknown observation type'):
        agent._get_observation_message(obs)


def test_user_reject_observation_message(agent: ProxyAgent):
    obs = UserRejectObservation('Action rejected')

    message = agent._get_observation_message(obs)

    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'system'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)
    assert (
        message.content[0].text
        == 'OBSERVATION:\nAction rejected\n[Last action has been rejected by the user]'
    )


def test_user_cmd_output_observation_message(agent: ProxyAgent):
    obs = CmdOutputObservation(
        command='echo hello',
        content='Command output',
        metadata=CmdOutputMetadata(
            exit_code=0,
            prefix='[THIS IS PREFIX]',
            suffix='[THIS IS SUFFIX]',
        ),
    )

    message = agent._get_observation_message(obs)

    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'system'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    assert 'Observed result of command executed by user:' in message.content[0].text
    assert '[Command finished with exit code 0]' in message.content[0].text
    assert '[THIS IS PREFIX]' in message.content[0].text
    assert '[THIS IS SUFFIX]' in message.content[0].text


def test_user_cmd_action_message(agent: ProxyAgent):
    action = CmdRunAction(command='ls -l')
    action._source = EventSource.USER

    message = agent._get_action_message(action)
    assert message is not None
    assert isinstance(message, Message)
    assert message.role == 'user'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    assert 'User executed the command' in message.content[0].text
    assert 'ls -l' in message.content[0].text


def test_get_tools():
    tools = get_tools()

    assert len(tools) > 0

    # Check required tools are present
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'delegate_local' in tool_names
    assert 'delegate_remote_oh' in tool_names
    assert 'finish' in tool_names


def test_delegate_local_tool():
    assert DelegateLocalTool['type'] == 'function'
    assert DelegateLocalTool['function']['name'] == 'delegate_local'
    assert list(DelegateLocalTool['function']['parameters']['properties'].keys()) == [
        'agent_name',
        'task',
    ]
    assert DelegateLocalTool['function']['parameters']['required'] == [
        'agent_name',
        'task',
    ]


def test_delegate_remote_oh_tool():
    assert DelegateRemoteOHTool['type'] == 'function'
    assert DelegateRemoteOHTool['function']['name'] == 'delegate_remote_oh'
    assert list(
        DelegateRemoteOHTool['function']['parameters']['properties'].keys()
    ) == ['url', 'agent_name', 'task', 'conversation_id']
    assert DelegateRemoteOHTool['function']['parameters']['required'] == [
        'url',
        'agent_name',
        'task',
    ]


def test_finish_tool():
    assert FinishTool['type'] == 'function'
    assert FinishTool['function']['name'] == 'finish'


def test_response_to_action_invalid_tool():
    # Test response with invalid tool call
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = 'Invalid tool'
    mock_response.choices[0].message.tool_calls = [Mock()]
    mock_response.choices[0].message.tool_calls[0].id = 'tool_call_10'
    mock_response.choices[0].message.tool_calls[0].function = Mock()
    mock_response.choices[0].message.tool_calls[0].function.name = 'invalid_tool'
    mock_response.choices[0].message.tool_calls[0].function.arguments = '{}'

    with pytest.raises(FunctionCallNotExistsError):
        response_to_action(mock_response)


def test_step(mock_state: State):
    # Mock the LLM response
    mock_response = Mock()
    mock_response.id = 'mock_id'
    mock_response.total_calls_in_response = 1
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = 'Task completed'
    mock_response.choices[0].message.tool_calls = []

    llm = Mock()
    llm.completion = Mock(return_value=mock_response)
    llm.is_function_calling_active = Mock(return_value=True)  # Enable function calling
    llm.is_caching_prompt_active = Mock(return_value=False)

    # Create agent with mocked LLM
    config = AgentConfig()
    config.enable_prompt_extensions = False
    agent = ProxyAgent(llm=llm, config=config)

    # Test step with no pending actions
    mock_state.latest_user_message = None
    mock_state.latest_user_message_id = None
    mock_state.latest_user_message_timestamp = None
    mock_state.latest_user_message_cause = None
    mock_state.latest_user_message_timeout = None
    mock_state.latest_user_message_llm_metrics = None
    mock_state.latest_user_message_tool_call_metadata = None

    action = agent.step(mock_state)
    assert isinstance(action, MessageAction)
    assert action.content == 'Task completed'
