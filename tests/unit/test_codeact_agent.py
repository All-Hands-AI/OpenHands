from unittest.mock import Mock

import pytest

from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.function_calling import (
    _BROWSER_DESCRIPTION,
    _BROWSER_TOOL_DESCRIPTION,
    BrowserTool,
    CmdRunTool,
    IPythonTool,
    LLMBasedFileEditTool,
    StrReplaceEditorTool,
    WebReadTool,
    get_tools,
    response_to_actions,
)
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.exceptions import FunctionCallNotExistsError
from openhands.core.message import ImageContent, TextContent
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import EventSource, FileEditSource, FileReadSource
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.events.observation.commands import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import FileEditObservation, FileReadObservation
from openhands.events.observation.reject import UserRejectObservation
from openhands.events.tool import ToolCallMetadata
from openhands.llm.llm import LLM


@pytest.fixture
def agent() -> CodeActAgent:
    agent = CodeActAgent(llm=LLM(LLMConfig()), config=AgentConfig())
    agent.llm = Mock()
    agent.llm.config = Mock()
    agent.llm.config.max_message_chars = 100
    return agent


def test_cmd_output_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = CmdOutputObservation(
        command='echo hello', content='Command output', command_id=1, exit_code=0
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Command output' in result.content[0].text
    assert 'Command finished with exit code 0' in result.content[0].text


def test_ipython_run_cell_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = IPythonRunCellObservation(
        code='plt.plot()',
        content='IPython output\n![image](data:image/png;base64,ABC123)',
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'IPython output' in result.content[0].text
    assert (
        '![image](data:image/png;base64, ...) already displayed to user'
        in result.content[0].text
    )
    assert 'ABC123' not in result.content[0].text


def test_agent_delegate_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Delegated agent output' in result.content[0].text


def test_error_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = ErrorObservation('Error message')

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Error message' in result.content[0].text
    assert 'Error occurred in processing last action' in result.content[0].text


def test_unknown_observation_message(agent: CodeActAgent):
    obs = Mock()

    with pytest.raises(ValueError, match='Unknown observation type'):
        agent.get_observation_message(obs, tool_call_id_to_message={})


def test_file_edit_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='old content',
        new_content='new content',
        content='diff content',
        impl_source=FileEditSource.LLM_BASED_EDIT,
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Existing file /test/file.txt is edited with' in result.content[0].text


def test_file_read_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = FileReadObservation(
        path='/test/file.txt',
        content='File content',
        impl_source=FileReadSource.DEFAULT,
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == 'File content'


def test_browser_output_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = BrowserOutputObservation(
        url='http://example.com',
        trigger_by_action='browse',
        screenshot='',
        content='Page loaded',
        error=False,
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Current URL: http://example.com]' in result.content[0].text


def test_user_reject_observation_message(agent: CodeActAgent):
    agent.config.function_calling = False
    obs = UserRejectObservation('Action rejected')

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Action rejected' in result.content[0].text
    assert '[Last action has been rejected by the user]' in result.content[0].text


def test_function_calling_observation_message(agent: CodeActAgent):
    agent.config.function_calling = True
    mock_response = {
        'id': 'mock_id',
        'total_calls_in_response': 1,
        'choices': [{'message': {'content': 'Task completed'}}],
    }
    obs = CmdOutputObservation(
        command='echo hello',
        content='Command output',
        command_id=1,
        exit_code=0,
    )
    obs.tool_call_metadata = ToolCallMetadata(
        tool_call_id='123',
        function_name='execute_bash',
        model_response=mock_response,
        total_calls_in_response=1,
    )

    results = agent.get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 0  # No direct message when using function calling


def test_message_action_with_image(agent: CodeActAgent):
    action = MessageAction(
        content='Message with image',
        image_urls=['http://example.com/image.jpg'],
    )
    action._source = EventSource.AGENT

    results = agent.get_action_message(action, {})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'assistant'
    assert len(result.content) == 2
    assert isinstance(result.content[0], TextContent)
    assert isinstance(result.content[1], ImageContent)
    assert result.content[0].text == 'Message with image'
    assert result.content[1].image_urls == ['http://example.com/image.jpg']


def test_user_cmd_action_message(agent: CodeActAgent):
    action = CmdRunAction(command='ls -l')
    action._source = EventSource.USER

    results = agent.get_action_message(action, {})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'User executed the command' in result.content[0].text
    assert 'ls -l' in result.content[0].text


def test_agent_finish_action_with_tool_metadata(agent: CodeActAgent):
    mock_response = {
        'id': 'mock_id',
        'total_calls_in_response': 1,
        'choices': [{'message': {'content': 'Task completed'}}],
    }

    action = AgentFinishAction(thought='Initial thought')
    action._source = EventSource.AGENT
    action.tool_call_metadata = ToolCallMetadata(
        tool_call_id='123',
        function_name='finish',
        model_response=mock_response,
        total_calls_in_response=1,
    )

    results = agent.get_action_message(action, {})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'assistant'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Initial thought\nTask completed' in result.content[0].text


def test_reset(agent: CodeActAgent):
    # Add some state
    action = MessageAction(content='test')
    action._source = EventSource.AGENT
    agent.pending_actions.append(action)

    # Reset
    agent.reset()

    # Verify state is cleared
    assert len(agent.pending_actions) == 0


def test_step_with_pending_actions(agent: CodeActAgent):
    # Add a pending action
    pending_action = MessageAction(content='test')
    pending_action._source = EventSource.AGENT
    agent.pending_actions.append(pending_action)

    # Step should return the pending action
    result = agent.step(Mock())
    assert result == pending_action
    assert len(agent.pending_actions) == 0


def test_get_tools_default():
    tools = get_tools(
        codeact_enable_jupyter=True,
        codeact_enable_llm_editor=True,
        codeact_enable_browsing=True,
    )
    assert len(tools) > 0

    # Check required tools are present
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'execute_bash' in tool_names
    assert 'execute_ipython_cell' in tool_names
    assert 'edit_file' in tool_names
    assert 'web_read' in tool_names


def test_get_tools_with_options():
    # Test with all options enabled
    tools = get_tools(
        codeact_enable_browsing=True,
        codeact_enable_jupyter=True,
        codeact_enable_llm_editor=True,
    )
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'browser' in tool_names
    assert 'execute_ipython_cell' in tool_names
    assert 'edit_file' in tool_names

    # Test with all options disabled
    tools = get_tools(
        codeact_enable_browsing=False,
        codeact_enable_jupyter=False,
        codeact_enable_llm_editor=False,
    )
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'browser' not in tool_names
    assert 'execute_ipython_cell' not in tool_names
    assert 'edit_file' not in tool_names


def test_cmd_run_tool():
    assert CmdRunTool['type'] == 'function'
    assert CmdRunTool['function']['name'] == 'execute_bash'
    assert 'command' in CmdRunTool['function']['parameters']['properties']
    assert CmdRunTool['function']['parameters']['required'] == ['command']


def test_ipython_tool():
    assert IPythonTool['type'] == 'function'
    assert IPythonTool['function']['name'] == 'execute_ipython_cell'
    assert 'code' in IPythonTool['function']['parameters']['properties']
    assert IPythonTool['function']['parameters']['required'] == ['code']


def test_llm_based_file_edit_tool():
    assert LLMBasedFileEditTool['type'] == 'function'
    assert LLMBasedFileEditTool['function']['name'] == 'edit_file'

    properties = LLMBasedFileEditTool['function']['parameters']['properties']
    assert 'path' in properties
    assert 'content' in properties
    assert 'start' in properties
    assert 'end' in properties

    assert LLMBasedFileEditTool['function']['parameters']['required'] == [
        'path',
        'content',
    ]


def test_str_replace_editor_tool():
    assert StrReplaceEditorTool['type'] == 'function'
    assert StrReplaceEditorTool['function']['name'] == 'str_replace_editor'

    properties = StrReplaceEditorTool['function']['parameters']['properties']
    assert 'command' in properties
    assert 'path' in properties
    assert 'file_text' in properties
    assert 'old_str' in properties
    assert 'new_str' in properties
    assert 'insert_line' in properties
    assert 'view_range' in properties

    assert StrReplaceEditorTool['function']['parameters']['required'] == [
        'command',
        'path',
    ]


def test_web_read_tool():
    assert WebReadTool['type'] == 'function'
    assert WebReadTool['function']['name'] == 'web_read'
    assert 'url' in WebReadTool['function']['parameters']['properties']
    assert WebReadTool['function']['parameters']['required'] == ['url']


def test_browser_tool():
    assert BrowserTool['type'] == 'function'
    assert BrowserTool['function']['name'] == 'browser'
    assert 'code' in BrowserTool['function']['parameters']['properties']
    assert BrowserTool['function']['parameters']['required'] == ['code']
    # Check that the description includes all the functions
    description = _BROWSER_TOOL_DESCRIPTION
    assert 'goto(' in description
    assert 'go_back()' in description
    assert 'go_forward()' in description
    assert 'noop(' in description
    assert 'scroll(' in description
    assert 'fill(' in description
    assert 'select_option(' in description
    assert 'click(' in description
    assert 'dblclick(' in description
    assert 'hover(' in description
    assert 'press(' in description
    assert 'focus(' in description
    assert 'clear(' in description
    assert 'drag_and_drop(' in description
    assert 'upload_file(' in description

    # Test BrowserTool definition
    assert BrowserTool['type'] == 'function'
    assert BrowserTool['function']['name'] == 'browser'
    assert BrowserTool['function']['description'] == _BROWSER_DESCRIPTION
    assert BrowserTool['function']['parameters']['type'] == 'object'
    assert 'code' in BrowserTool['function']['parameters']['properties']
    assert BrowserTool['function']['parameters']['required'] == ['code']
    assert (
        BrowserTool['function']['parameters']['properties']['code']['type'] == 'string'
    )
    assert 'description' in BrowserTool['function']['parameters']['properties']['code']


def test_mock_function_calling():
    # Test mock function calling when LLM doesn't support it
    llm = Mock()
    llm.is_function_calling_active = lambda: False
    config = AgentConfig()
    config.use_microagents = False
    agent = CodeActAgent(llm=llm, config=config)
    assert agent.mock_function_calling is True


def test_response_to_actions_invalid_tool():
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
        response_to_actions(mock_response)


def test_step_with_no_pending_actions():
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
    config.use_microagents = False
    agent = CodeActAgent(llm=llm, config=config)

    # Test step with no pending actions
    state = Mock()
    state.history = []
    state.latest_user_message = None
    state.latest_user_message_id = None
    state.latest_user_message_timestamp = None
    state.latest_user_message_cause = None
    state.latest_user_message_timeout = None
    state.latest_user_message_llm_metrics = None
    state.latest_user_message_tool_call_metadata = None

    action = agent.step(state)
    assert isinstance(action, MessageAction)
    assert action.content == 'Task completed'
