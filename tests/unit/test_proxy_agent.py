from unittest.mock import Mock

import pytest

from openhands.agenthub.proxy_agent.function_calling import (
    DelegateLocalTool,
    DelegateRemoteTool,
    FinishTool,
    get_tools,
    response_to_action,
)
from openhands.agenthub.proxy_agent.proxy_agent import ProxyAgent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.exceptions import FunctionCallNotExistsError
from openhands.events.action import (
    MessageAction,
)
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


def test_get_tools():
    tools = get_tools()

    assert len(tools) > 0

    # Check required tools are present
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'delegate_local' in tool_names
    assert 'delegate_remote' in tool_names
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


def test_delegate_remote_tool():
    assert DelegateRemoteTool['type'] == 'function'
    assert DelegateRemoteTool['function']['name'] == 'delegate_remote'
    assert list(DelegateRemoteTool['function']['parameters']['properties'].keys()) == [
        'url',
        'task',
        'session_id',
        'task_id',
    ]
    assert DelegateRemoteTool['function']['parameters']['required'] == [
        'url',
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
