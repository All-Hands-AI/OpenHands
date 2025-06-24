from unittest.mock import Mock

import pytest
from litellm import ChatCompletionMessageToolCall, ModelResponse

from openhands.agenthub.codeact_agent import function_calling
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.agenthub.codeact_agent.function_calling import (
    BrowserTool,
    IPythonTool,
    LLMBasedFileEditTool,
    WebReadTool,
    create_cmd_run_tool,
    create_str_replace_editor_tool,
    get_tools,
    response_to_actions,
)
from openhands.agenthub.codeact_agent.tools.browser import (
    _BROWSER_DESCRIPTION,
    _BROWSER_TOOL_DESCRIPTION,
)
from openhands.agenthub.codeact_agent.tools.finish import FinishTool
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.message import ImageContent, Message, TextContent
from openhands.core.schema.research import ResearchMode
from openhands.events.action import (
    CmdRunAction,
    MessageAction,
)
from openhands.events.action.agent import AgentThinkAction
from openhands.events.event import EventSource
from openhands.events.observation.commands import (
    CmdOutputObservation,
)
from openhands.events.tool import ToolCallMetadata
from openhands.llm.llm import LLM


@pytest.fixture
def agent() -> CodeActAgent:
    config = AgentConfig()
    agent = CodeActAgent(llm=LLM(LLMConfig()), config=config)
    agent.llm = Mock()
    agent.llm.config = Mock()
    agent.llm.config.max_message_chars = 1000
    agent.llm.config.model = 'claude-3-5-sonnet-20241022'  # Set a valid model name
    return agent


@pytest.fixture
def mock_state() -> State:
    state = Mock(spec=State)
    state.history = []
    state.extra_data = {}

    return state


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
    CmdRunTool = create_cmd_run_tool()
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
    StrReplaceEditorTool = create_str_replace_editor_tool()
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


def test_response_to_actions_invalid_tool():
    # Test response with invalid tool call
    mock_response = ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': {
                    'content': 'Invalid tool',
                    'tool_calls': [
                        {
                            'id': 'tool_call_10',
                            'function': {'name': 'invalid_tool', 'arguments': '{}'},
                        }
                    ],
                }
            }
        ],
    )

    action = response_to_actions(mock_response)
    assert isinstance(action[0], AgentThinkAction)
    print(action[0].thought)
    assert (
        action[0].thought
        == 'Invalid tool\nTool invalid_tool is not registered. (arguments: {}). Please check the tool name and retry with an existing tool.'
    )


def test_step_with_no_pending_actions(mock_state: State):
    # Mock the LLM response
    mock_response = Mock()
    mock_response.id = 'mock_id'
    mock_response.total_calls_in_response = 1
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = 'Task completed'
    mock_response.choices[0].message.tool_calls = []

    mock_config = Mock()
    mock_config.model = 'mock_model'

    llm = Mock()
    llm.config = mock_config
    llm.completion = Mock(return_value=mock_response)
    llm.is_function_calling_active = Mock(return_value=True)  # Enable function calling
    llm.is_caching_prompt_active = Mock(return_value=False)

    # Create agent with mocked LLM
    config = AgentConfig()
    config.enable_prompt_extensions = False
    agent = CodeActAgent(llm=llm, config=config)

    # Test step with no pending actions
    mock_state.latest_user_message = None
    mock_state.latest_user_message_id = None
    mock_state.latest_user_message_timestamp = None
    mock_state.latest_user_message_cause = None
    mock_state.latest_user_message_timeout = None
    mock_state.latest_user_message_llm_metrics = None
    mock_state.latest_user_message_tool_call_metadata = None

    action = agent.step(mock_state)
    assert action is None or (
        isinstance(action, MessageAction) and action.content == 'Task completed'
    )


def test_correct_tool_description_loaded_based_on_model_name(mock_state: State):
    """Tests that the simplified tool descriptions are loaded for specific models."""
    o3_mock_config = Mock()
    o3_mock_config.model = 'mock_o3_model'
    o3_mock_config.log_completions_folder = (
        '/tmp/test_completions'  # Add required config
    )
    o3_mock_config.max_message_chars = 1000  # Add required config

    llm = Mock()
    llm.config = o3_mock_config

    agent = CodeActAgent(llm=llm, config=AgentConfig())
    for tool in agent.tools:
        # Assert all descriptions have less than 1024 characters
        assert len(tool['function']['description']) < 1024

    sonnet_mock_config = Mock()
    sonnet_mock_config.model = 'mock_sonnet_model'
    sonnet_mock_config.log_completions_folder = (
        '/tmp/test_completions'  # Add required config
    )
    sonnet_mock_config.max_message_chars = 1000  # Add required config

    llm.config = sonnet_mock_config
    agent = CodeActAgent(llm=llm, config=AgentConfig())
    # Assert existence of the detailed tool descriptions that are longer than 1024 characters
    assert any(len(tool['function']['description']) > 1024 for tool in agent.tools)


def test_mismatched_tool_call_events(mock_state: State):
    """Tests that the agent can convert mismatched tool call events (i.e., an observation with no corresponding action) into messages."""
    agent = CodeActAgent(llm=LLM(LLMConfig()), config=AgentConfig())

    tool_call_metadata = Mock(
        spec=ToolCallMetadata,
        model_response=Mock(
            id='model_response_0',
            choices=[
                Mock(
                    message=Mock(
                        role='assistant',
                        content='',
                        tool_calls=[
                            Mock(spec=ChatCompletionMessageToolCall, id='tool_call_0')
                        ],
                    )
                )
            ],
        ),
        tool_call_id='tool_call_0',
        function_name='foo',
    )

    action = CmdRunAction('foo')
    action._source = 'agent'
    action.tool_call_metadata = tool_call_metadata

    observation = CmdOutputObservation(content='', command_id=0, command='foo')
    observation.tool_call_metadata = tool_call_metadata

    # When both events are provided, the agent should get three messages:
    # 1. The system message,
    # 2. The action message, and
    # 3. The observation message
    mock_state.history = [action, observation]
    messages = agent._get_messages(mock_state.history)
    assert len(messages) == 3

    # The same should hold if the events are presented out-of-order
    mock_state.history = [observation, action]
    messages = agent._get_messages(mock_state.history)
    assert len(messages) == 3

    # If only one of the two events is present, then we should just get the system message
    mock_state.history = [action]
    messages = agent._get_messages(mock_state.history)
    assert len(messages) == 1

    mock_state.history = [observation]
    messages = agent._get_messages(mock_state.history)
    assert len(messages) == 1


def test_enhance_messages_adds_newlines_between_consecutive_user_messages(
    agent: CodeActAgent,
):
    """Test that _enhance_messages adds newlines between consecutive user messages."""
    # Set up the prompt manager
    agent.prompt_manager = Mock()
    agent.prompt_manager.add_examples_to_initial_message = Mock()
    agent.prompt_manager.add_info_to_initial_message = Mock()
    agent.prompt_manager.enhance_message = Mock()

    # Create consecutive user messages with various content types
    messages = [
        # First user message with TextContent only
        Message(role='user', content=[TextContent(text='First user message')]),
        # Second user message with TextContent only - should get newlines added
        Message(role='user', content=[TextContent(text='Second user message')]),
        # Assistant message
        Message(role='assistant', content=[TextContent(text='Assistant response')]),
        # Third user message with TextContent only - shouldn't get newlines
        Message(role='user', content=[TextContent(text='Third user message')]),
        # Fourth user message with ImageContent first, TextContent second - should get newlines
        Message(
            role='user',
            content=[
                ImageContent(image_urls=['https://example.com/image.jpg']),
                TextContent(text='Fourth user message with image'),
            ],
        ),
        # Fifth user message with only ImageContent - no TextContent to modify
        Message(
            role='user',
            content=[
                ImageContent(image_urls=['https://example.com/another-image.jpg'])
            ],
        ),
    ]

    # Call _enhance_messages
    enhanced_messages = agent._enhance_messages(messages)

    # Verify newlines were added correctly
    assert enhanced_messages[1].content[0].text.startswith('\n\n')
    assert enhanced_messages[1].content[0].text == '\n\nSecond user message'

    # Third message follows assistant, so shouldn't have newlines
    assert not enhanced_messages[3].content[0].text.startswith('\n\n')
    assert enhanced_messages[3].content[0].text == 'Third user message'

    # Fourth message follows user, so should have newlines in its TextContent
    assert enhanced_messages[4].content[1].text.startswith('\n\n')
    assert enhanced_messages[4].content[1].text == '\n\nFourth user message with image'

    # Fifth message only has ImageContent, no TextContent to modify
    assert len(enhanced_messages[5].content) == 1
    assert isinstance(enhanced_messages[5].content[0], ImageContent)


def test_select_tools_based_on_mode_chat_mode(agent: CodeActAgent):
    """Test tool selection in CHAT mode."""
    # Mock MCP tools
    agent.mcp_tools = [
        {
            'function': {
                'name': 'pyodide_execute_bash_mcp_tool_call',
                'description': 'Execute bash command',
            }
        },
        {
            'function': {
                'name': 'pyodide_str_replace_editor_mcp_tool_call',
                'description': 'Edit file',
            }
        },
    ]
    agent.config.enable_pyodide = True

    # Mock search tools
    agent.search_tools = [
        {'function': {'name': 'search_tool', 'description': 'Search tool'}}
    ]

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Should include simplified tools, pyodide tools, and search tools
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'search_tool' in tool_names
    assert 'think' in tool_names
    assert 'finish' in tool_names


def test_select_tools_based_on_mode_follow_up_mode(agent: CodeActAgent):
    """Test tool selection in FOLLOW_UP mode."""
    # Mock MCP tools
    agent.mcp_tools = [
        {
            'function': {
                'name': 'pyodide_execute_bash_mcp_tool_call',
                'description': 'Execute bash command',
            }
        }
    ]

    agent.config.enable_pyodide = False

    # Test with FOLLOW_UP mode
    tools = agent._select_tools_based_on_mode(ResearchMode.FOLLOW_UP)

    # Should only include FinishTool
    assert len(tools) == 1
    assert tools[0] == FinishTool


def test_select_tools_based_on_mode_no_mcp_tools(agent: CodeActAgent):
    """Test tool selection when no MCP tools are available."""
    agent.mcp_tools = None
    agent.search_tools = [
        {'function': {'name': 'search_tool', 'description': 'Search tool'}}
    ]

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Should include base tools and search tools
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'search_tool' in tool_names
    assert 'execute_bash' in tool_names
    assert 'think' in tool_names
    assert 'finish' in tool_names
    assert 'str_replace_editor' in tool_names
    assert len(tools) > 1  # Should have base tools plus search tools


def test_select_tools_based_on_mode_missing_pyodide_tools(agent: CodeActAgent):
    """Test tool selection when some pyodide tools are missing."""
    # Mock MCP tools with only bash tool
    agent.mcp_tools = [
        {
            'function': {
                'name': 'pyodide_execute_bash_mcp_tool_call',
                'description': 'Execute bash command',
            }
        }
    ]
    agent.search_tools = [
        {'function': {'name': 'search_tool', 'description': 'Search tool'}}
    ]

    agent.tools = function_calling.get_tools(
        codeact_enable_browsing=agent.config.codeact_enable_browsing,
        codeact_enable_jupyter=agent.config.codeact_enable_jupyter,
        codeact_enable_llm_editor=agent.config.codeact_enable_llm_editor,
        llm=None,
        enable_pyodide_bash=True,
    )

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Should not fall back to base tools since there are pyodide tools present
    assert len(tools) == 4
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'think' in tool_names
    assert 'finish' in tool_names
    assert 'search_tool' in tool_names
    assert 'str_replace_editor' in tool_names


def test_select_tools_based_on_mode_duplicate_tools(agent: CodeActAgent):
    """Test tool selection with duplicate tool names."""
    # Mock MCP tools with duplicate names
    agent.mcp_tools = [
        {
            'function': {
                'name': 'duplicate_tool_mcp_tool_call',
                'description': 'First tool',
            }
        },
        {
            'function': {
                'name': 'duplicate_tool_mcp_tool_call',
                'description': 'Second tool',
            }
        },
    ]

    # Add duplicate to base tools
    agent.tools = [
        {
            'function': {
                'name': 'duplicate_tool_mcp_tool_call',
                'description': 'Base tool',
            }
        }
    ]

    # Test with other mode
    tools = agent._select_tools_based_on_mode('OTHER_MODE')

    # Should deduplicate tools
    tool_names = [tool['function']['name'] for tool in tools]
    assert tool_names.count('duplicate_tool_mcp_tool_call') == 1


def test_select_tools_based_on_mode_deep_research(agent: CodeActAgent):
    """Test tool selection in DEEP_RESEARCH mode."""
    # Mock MCP tools
    agent.mcp_tools = [
        {
            'function': {
                'name': 'mcp_tool_1',
                'description': 'MCP tool 1',
            }
        },
        {
            'function': {
                'name': 'mcp_tool_2',
                'description': 'MCP tool 2',
            }
        },
    ]

    # Mock search tools
    agent.search_tools = [
        {'function': {'name': 'search_tool_1', 'description': 'Search tool 1'}},
        {'function': {'name': 'search_tool_2', 'description': 'Search tool 2'}},
    ]

    # Enable A2A server URLs
    agent.config.a2a_server_urls = ['http://example.com']

    # Test with DEEP_RESEARCH mode
    tools = agent._select_tools_based_on_mode(ResearchMode.DEEP_RESEARCH)

    # Should include all tools
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'mcp_tool_1' in tool_names
    assert 'mcp_tool_2' in tool_names
    assert 'search_tool_1' in tool_names
    assert 'search_tool_2' in tool_names
    assert 'a2a_list_remote_agents' in tool_names
    assert 'a2a_send_task' in tool_names
    assert 'think' in tool_names
    assert 'finish' in tool_names


def test_select_tools_based_on_mode_cache_control(agent: CodeActAgent):
    """Test cache control setting for Claude models."""
    # Set model to Claude
    agent.llm.config.model = 'claude-3-5-sonnet-20241022'

    # Mock tools with multiple cache controls
    agent.tools = [
        {
            'function': {'name': 'tool1', 'description': 'Tool 1'},
            'cache_control': {'type': 'ephemeral'},
        },
        {
            'function': {'name': 'tool2', 'description': 'Tool 2'},
            'cache_control': {'type': 'ephemeral'},
        },
        {
            'function': {'name': 'tool3', 'description': 'Tool 3'},
            'cache_control': {'type': 'ephemeral'},
        },
    ]

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Check only the last tool has cache control
    assert 'cache_control' in tools[-1]
    assert tools[-1]['cache_control'] == {'type': 'ephemeral'}

    # Check other tools don't have cache control
    for tool in tools[:-1]:
        assert 'cache_control' not in tool

    # Test with single tool
    agent.tools = [
        {'function': {'name': 'tool1', 'description': 'Tool 1'}},
        {'function': {'name': 'tool2', 'description': 'Tool 2'}},
    ]

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Check cache control is set on last tool
    assert 'cache_control' in tools[-1]
    assert tools[-1]['cache_control'] == {'type': 'ephemeral'}

    # Check other tools don't have cache control
    for tool in tools[:-1]:
        assert 'cache_control' not in tool


def test_select_tools_based_on_mode_non_claude(agent: CodeActAgent):
    """Test tool selection for non-Claude models."""
    # Set model to non-Claude
    agent.llm.config.model = 'gpt-4'

    # Mock tools
    agent.tools = [
        {'function': {'name': 'tool1', 'description': 'Tool 1'}},
        {'function': {'name': 'tool2', 'description': 'Tool 2'}},
    ]

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Check no cache control is set
    for tool in tools:
        assert 'cache_control' not in tool


def test_select_tools_based_on_mode_empty_tools(agent: CodeActAgent):
    """Test tool selection with empty tool sets."""
    # Set empty tool sets
    agent.tools = []
    agent.mcp_tools = []
    agent.search_tools = []

    # Test with CHAT mode
    tools = agent._select_tools_based_on_mode(ResearchMode.CHAT)

    # Should return empty list
    assert len(tools) == 0


def test_select_tools_based_on_mode_a2a_tools(agent: CodeActAgent):
    """Test A2A tools are included when a2a_server_urls is set."""
    # Enable A2A server URLs
    agent.config.a2a_server_urls = ['http://example.com']

    # Test with DEEP_RESEARCH mode
    tools = agent._select_tools_based_on_mode(ResearchMode.DEEP_RESEARCH)

    # Should include A2A tools
    tool_names = [tool['function']['name'] for tool in tools]
    assert 'a2a_list_remote_agents' in tool_names
    assert 'a2a_send_task' in tool_names


def test_mcp_tool_not_found():
    """Test that MCP tool not found returns AgentThinkAction instead of raising error."""
    # Test response with MCP tool call that's not in available tools
    mock_response = ModelResponse(
        id='mock-id',
        choices=[
            {
                'message': {
                    'content': 'Using MCP tool',
                    'tool_calls': [
                        {
                            'id': 'tool_call_10',
                            'function': {
                                'name': 'unavailable_tool_mcp_tool_call',
                                'arguments': '{"arg1": "value1"}',
                            },
                        }
                    ],
                }
            }
        ],
    )

    # Available tools list without the MCP tool
    available_tools = [
        {'function': {'name': 'execute_bash', 'description': 'Execute bash command'}},
        {'function': {'name': 'think', 'description': 'Think'}},
    ]

    actions = response_to_actions(mock_response, tools=available_tools)
    assert len(actions) == 1
    assert isinstance(actions[0], AgentThinkAction)
    assert (
        'MCP tool unavailable_tool_mcp_tool_call is not available' in actions[0].thought
    )
    assert (
        'Please check the available tools and retry with an existing tool'
        in actions[0].thought
    )


def test_stream_function_message_simple_case(agent: CodeActAgent):
    """Test streaming a simple finish/think function message."""
    # Mock event stream
    agent.event_stream = Mock()

    streaming_calls = {}

    # Test complete message in one chunk
    chunk = '{"message": "Hello world"}'
    agent._stream_function_message('tool_1', chunk, streaming_calls, None)

    # Should find message start and emit content
    assert streaming_calls['tool_1']['msg_start'] != -1
    assert agent.event_stream.add_event.called

    # Check the emitted content
    call_args = agent.event_stream.add_event.call_args[0]
    action = call_args[0]
    assert action.content == 'Hello world'


def test_stream_function_message_chunked_pattern(agent: CodeActAgent):
    """Test streaming when the "message": pattern is split across chunks."""
    agent.event_stream = Mock()
    streaming_calls = {}

    # Chunk 1: partial pattern
    agent._stream_function_message('tool_1', '{"mess', streaming_calls, None)
    assert streaming_calls['tool_1']['msg_start'] == -1  # Not found yet
    assert not agent.event_stream.add_event.called

    # Chunk 2: complete pattern + content start
    agent._stream_function_message('tool_1', 'age": "Hello', streaming_calls, None)
    assert streaming_calls['tool_1']['msg_start'] != -1  # Found now
    assert agent.event_stream.add_event.called

    # Reset mock for next test
    agent.event_stream.add_event.reset_mock()

    # Chunk 3: more content
    agent._stream_function_message('tool_1', ' world"', streaming_calls, None)
    assert agent.event_stream.add_event.called


def test_stream_function_message_whitespace_variations(agent: CodeActAgent):
    """Test handling different whitespace variations in message pattern."""
    agent.event_stream = Mock()
    test_cases = [
        '"message":"Hello"',
        '"message" :"Hello"',
        '"message": "Hello"',
        '"message" : "Hello"',
    ]

    for i, chunk in enumerate(test_cases):
        streaming_calls = {}
        tool_id = f'tool_{i}'

        agent._stream_function_message(tool_id, chunk, streaming_calls)

        assert streaming_calls[tool_id]['msg_start'] != -1
        assert agent.event_stream.add_event.called

        # Check content was extracted correctly
        call_args = agent.event_stream.add_event.call_args[0]
        action = call_args[0]
        assert action.content == 'Hello'

        agent.event_stream.add_event.reset_mock()


def test_stream_function_message_json_escapes(agent: CodeActAgent):
    """Test handling of JSON escape sequences."""
    agent.event_stream = Mock()
    streaming_calls = {}

    # Test with escaped quotes and newlines
    chunk = '{"message": "He said \\"Hello\\nWorld\\""}'
    agent._stream_function_message('tool_1', chunk, streaming_calls)

    assert agent.event_stream.add_event.called
    call_args = agent.event_stream.add_event.call_args[0]
    action = call_args[0]
    # Should decode JSON escapes
    assert action.content == 'He said "Hello\nWorld"'


def test_stream_function_message_partial_escapes(agent: CodeActAgent):
    """Test that partial escape sequences are not streamed."""
    agent.event_stream = Mock()
    streaming_calls = {}

    # First chunk ends with backslash (partial escape)
    agent._stream_function_message('tool_1', '{"message": "Hello\\', streaming_calls)

    # Should not stream content ending with backslash
    if agent.event_stream.add_event.called:
        call_args = agent.event_stream.add_event.call_args[0]
        action = call_args[0]
        assert not action.content.endswith('\\')


def test_stream_function_message_unicode_escapes(agent: CodeActAgent):
    """Test handling of partial unicode escape sequences."""
    agent.event_stream = Mock()
    streaming_calls = {}

    # Test incomplete unicode escape
    agent._stream_function_message(
        'tool_1', '{"message": "Hello \\u12', streaming_calls
    )

    # Should not stream incomplete unicode
    if agent.event_stream.add_event.called:
        call_args = agent.event_stream.add_event.call_args[0]
        action = call_args[0]
        assert not action.content.endswith('\\u12')


def test_stream_function_message_multiple_chunks(agent: CodeActAgent):
    """Test streaming content across multiple chunks."""
    agent.event_stream = Mock()
    streaming_calls = {}

    chunks = [
        '{"message": "This is',
        ' a long message',
        ' that spans',
        ' multiple chunks"}',
    ]

    for chunk in chunks:
        agent._stream_function_message('tool_1', chunk, streaming_calls)

    # Should have been called multiple times
    assert agent.event_stream.add_event.call_count >= 1

    # Check that content is streamed incrementally
    state = streaming_calls['tool_1']
    assert (
        'This is a long message that spans multiple chunks'
        in state['buffer'][state['msg_start'] :]
    )


def test_get_safe_content(agent: CodeActAgent):
    """Test the _get_safe_content helper method."""
    # Test normal content
    assert agent._get_safe_content('Hello world') == 'Hello world'

    # Test empty content
    assert agent._get_safe_content('') == ''

    # Test content ending with backslash
    assert agent._get_safe_content('Hello\\') == 'Hello'
    assert agent._get_safe_content('\\') == ''

    # Test incomplete unicode
    assert agent._get_safe_content('Hello \\u12') == 'Hello '
    assert agent._get_safe_content('Hello \\u') == 'Hello '
    assert agent._get_safe_content('Hello \\u1') == 'Hello '
    assert agent._get_safe_content('Hello \\u123') == 'Hello '

    # Test complete unicode (should pass through)
    assert agent._get_safe_content('Hello \\u1234') == 'Hello \\u1234'


def test_find_unescaped_quote(agent: CodeActAgent):
    """Test the _find_unescaped_quote helper method."""
    # Test simple quote
    assert agent._find_unescaped_quote('Hello"world') == 5

    # Test escaped quote
    assert agent._find_unescaped_quote('Hello\\"world"') == 12

    # Test multiple escaped quotes
    assert agent._find_unescaped_quote('He said \\"Hello\\" to me"') == 23

    # Test no quote
    assert agent._find_unescaped_quote('Hello world') == -1

    # Test double backslash (not escaping quote)
    assert agent._find_unescaped_quote('Hello\\\\"world') == 7


def test_emit_streaming_content(agent: CodeActAgent):
    """Test the _emit_streaming_content method."""
    agent.event_stream = Mock()

    # Test valid content
    agent._emit_streaming_content('Hello world')
    assert agent.event_stream.add_event.called

    call_args = agent.event_stream.add_event.call_args[0]
    action = call_args[0]
    assert action.content == 'Hello world'
    assert action.wait_for_response is False

    # Test with JSON escapes
    agent.event_stream.add_event.reset_mock()
    agent._emit_streaming_content('Hello\\nworld')

    call_args = agent.event_stream.add_event.call_args[0]
    action = call_args[0]
    assert action.content == 'Hello\nworld'  # Should be decoded


def test_stream_function_message_no_event_stream(agent: CodeActAgent):
    """Test streaming when event_stream is None."""
    agent.event_stream = None
    streaming_calls = {}

    # Should not raise error
    agent._stream_function_message('tool_1', '{"message": "Hello"}', streaming_calls)

    # State should still be tracked
    assert 'tool_1' in streaming_calls
    assert streaming_calls['tool_1']['msg_start'] != -1


def test_stream_function_message_concurrent_calls(agent: CodeActAgent):
    """Test handling multiple concurrent function calls."""
    agent.event_stream = Mock()
    streaming_calls = {}

    # Simulate two concurrent tool calls
    agent._stream_function_message(
        'tool_1', '{"message": "Message 1"}', streaming_calls
    )
    agent._stream_function_message(
        'tool_2', '{"message": "Message 2"}', streaming_calls
    )

    # Both should be tracked separately
    assert 'tool_1' in streaming_calls
    assert 'tool_2' in streaming_calls
    assert streaming_calls['tool_1']['msg_start'] != -1
    assert streaming_calls['tool_2']['msg_start'] != -1

    # Both should emit content
    assert agent.event_stream.add_event.call_count == 2
