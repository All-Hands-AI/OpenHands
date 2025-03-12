from unittest.mock import MagicMock, Mock

import pytest

from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import Event, EventSource, FileEditSource, FileReadSource
from openhands.events.observation import CmdOutputObservation
from openhands.events.observation.agent import RecallObservation, RecallType
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import FileEditObservation, FileReadObservation
from openhands.events.observation.reject import UserRejectObservation
from openhands.events.tool import ToolCallMetadata
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager, RepositoryInfo, RuntimeInfo


@pytest.fixture
def agent_config():
    return AgentConfig(
        enable_prompt_extensions=True,
        enable_som_visual_browsing=True,
        disabled_microagents=['disabled_agent'],
    )


@pytest.fixture
def conversation_memory(agent_config):
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    prompt_manager.build_additional_info.return_value = (
        'Formatted repository and runtime info'
    )

    # Make build_microagent_info return the actual content from the triggered agents
    def build_microagent_info(triggered_agents):
        if not triggered_agents:
            return ''
        return '\n'.join(agent.content for agent in triggered_agents)

    prompt_manager.build_microagent_info.side_effect = build_microagent_info
    return ConversationMemory(agent_config, prompt_manager)


@pytest.fixture
def mock_state():
    state = MagicMock(spec=State)
    state.history = []
    return state


def test_process_initial_messages(conversation_memory):
    messages = conversation_memory.process_initial_messages(with_caching=False)
    assert len(messages) == 1
    assert messages[0].role == 'system'
    assert messages[0].content[0].text == 'System message'
    assert messages[0].content[0].cache_prompt is False

    messages = conversation_memory.process_initial_messages(with_caching=True)
    assert messages[0].content[0].cache_prompt is True


def test_process_events_with_message_action(conversation_memory):
    user_message = MessageAction(content='Hello')
    user_message._source = EventSource.USER
    assistant_message = MessageAction(content='Hi there')
    assistant_message._source = EventSource.AGENT

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[user_message, assistant_message],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 3
    assert messages[0].role == 'system'
    assert messages[1].role == 'user'
    assert messages[1].content[0].text == 'Hello'
    assert messages[2].role == 'assistant'
    assert messages[2].content[0].text == 'Hi there'


def test_process_events_with_cmd_output_observation(conversation_memory):
    obs = CmdOutputObservation(
        command='echo hello',
        content='Command output',
        metadata=CmdOutputMetadata(
            exit_code=0,
            prefix='[THIS IS PREFIX]',
            suffix='[THIS IS SUFFIX]',
        ),
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Observed result of command executed by user:' in result.content[0].text
    assert '[Command finished with exit code 0]' in result.content[0].text
    assert '[THIS IS PREFIX]' in result.content[0].text
    assert '[THIS IS SUFFIX]' in result.content[0].text


def test_process_events_with_ipython_run_cell_observation(conversation_memory):
    obs = IPythonRunCellObservation(
        code='plt.plot()',
        content='IPython output\n![image](data:image/png;base64,ABC123)',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'IPython output' in result.content[0].text
    assert (
        '![image](data:image/png;base64, ...) already displayed to user'
        in result.content[0].text
    )
    assert 'ABC123' not in result.content[0].text


def test_process_events_with_agent_delegate_observation(conversation_memory):
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Delegated agent output' in result.content[0].text


def test_process_events_with_error_observation(conversation_memory):
    obs = ErrorObservation('Error message')

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Error message' in result.content[0].text
    assert 'Error occurred in processing last action' in result.content[0].text


def test_process_events_with_unknown_observation(conversation_memory):
    # Create a mock that inherits from Event but not Action or Observation
    obs = Mock(spec=Event)

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    with pytest.raises(ValueError, match='Unknown event type'):
        conversation_memory.process_events(
            condensed_history=[obs],
            initial_messages=initial_messages,
            max_message_chars=None,
            vision_is_active=False,
        )


def test_process_events_with_file_edit_observation(conversation_memory):
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='old content',
        new_content='new content',
        content='diff content',
        impl_source=FileEditSource.LLM_BASED_EDIT,
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Existing file /test/file.txt is edited with' in result.content[0].text


def test_process_events_with_file_read_observation(conversation_memory):
    obs = FileReadObservation(
        path='/test/file.txt',
        content='File content',
        impl_source=FileReadSource.DEFAULT,
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == 'File content'


def test_process_events_with_browser_output_observation(conversation_memory):
    obs = BrowserOutputObservation(
        url='http://example.com',
        trigger_by_action='browse',
        screenshot='',
        content='Page loaded',
        error=False,
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Current URL: http://example.com]' in result.content[0].text


def test_process_events_with_user_reject_observation(conversation_memory):
    obs = UserRejectObservation('Action rejected')

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Action rejected' in result.content[0].text
    assert '[Last action has been rejected by the user]' in result.content[0].text


def test_process_events_with_function_calling_observation(conversation_memory):
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

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # No direct message when using function calling
    assert len(messages) == 1  # Only the initial system message


def test_process_events_with_message_action_with_image(conversation_memory):
    action = MessageAction(
        content='Message with image',
        image_urls=['http://example.com/image.jpg'],
    )
    action._source = EventSource.AGENT

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[action],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=True,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'assistant'
    assert len(result.content) == 2
    assert isinstance(result.content[0], TextContent)
    assert isinstance(result.content[1], ImageContent)
    assert result.content[0].text == 'Message with image'
    assert result.content[1].image_urls == ['http://example.com/image.jpg']


def test_process_events_with_user_cmd_action(conversation_memory):
    action = CmdRunAction(command='ls -l')
    action._source = EventSource.USER

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[action],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'User executed the command' in result.content[0].text
    assert 'ls -l' in result.content[0].text


def test_process_events_with_agent_finish_action_with_tool_metadata(
    conversation_memory,
):
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

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[action],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'assistant'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Initial thought\nTask completed' in result.content[0].text


def test_apply_prompt_caching(conversation_memory):
    messages = [
        Message(role='system', content=[TextContent(text='System message')]),
        Message(role='user', content=[TextContent(text='User message')]),
        Message(role='assistant', content=[TextContent(text='Assistant message')]),
        Message(role='user', content=[TextContent(text='Another user message')]),
    ]

    conversation_memory.apply_prompt_caching(messages)

    # Only the last user message should have cache_prompt=True
    assert messages[0].content[0].cache_prompt is False
    assert messages[1].content[0].cache_prompt is False
    assert messages[2].content[0].cache_prompt is False
    assert messages[3].content[0].cache_prompt is True


def test_process_events_with_environment_info_recall_observation(conversation_memory):
    """Test processing a RecallObservation with ENVIRONMENT_INFO type."""
    obs = RecallObservation(
        recall_type=RecallType.ENVIRONMENT_INFO,
        repo_name='test-repo',
        repo_directory='/path/to/repo',
        repo_instructions='# Test Repository\nThis is a test repository.',
        runtime_hosts={'localhost': 8080},
        content='Recalled environment info',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == 'Formatted repository and runtime info'

    # Verify the prompt_manager was called with the correct parameters
    conversation_memory.prompt_manager.build_additional_info.assert_called_once()
    call_args = conversation_memory.prompt_manager.build_additional_info.call_args[1]
    assert isinstance(call_args['repository_info'], RepositoryInfo)
    assert call_args['repository_info'].repo_name == 'test-repo'
    assert call_args['repository_info'].repo_directory == '/path/to/repo'
    assert isinstance(call_args['runtime_info'], RuntimeInfo)
    assert call_args['runtime_info'].available_hosts == {'localhost': 8080}
    assert (
        call_args['repo_instructions']
        == '# Test Repository\nThis is a test repository.'
    )


def test_process_events_with_knowledge_microagent_recall_observation(
    conversation_memory,
):
    """Test processing a RecallObservation with KNOWLEDGE_MICROAGENT type."""
    microagent_knowledge = [
        {
            'agent_name': 'test_agent',
            'trigger_word': 'test',
            'content': 'This is test agent content',
        },
        {
            'agent_name': 'another_agent',
            'trigger_word': 'another',
            'content': 'This is another agent content',
        },
        {
            'agent_name': 'disabled_agent',
            'trigger_word': 'disabled',
            'content': 'This is disabled agent content',
        },
    ]

    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=microagent_knowledge,
        content='Recalled knowledge from microagents',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    assert len(messages) == 2
    result = messages[1]
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    # Verify that disabled_agent is filtered out and enabled agents are included
    assert 'This is test agent content' in result.content[0].text
    assert 'This is another agent content' in result.content[0].text
    assert 'This is disabled agent content' not in result.content[0].text

    # Verify the prompt_manager was called with the correct parameters
    conversation_memory.prompt_manager.build_microagent_info.assert_called_once()
    call_args = conversation_memory.prompt_manager.build_microagent_info.call_args[1]

    # Check that disabled_agent was filtered out
    triggered_agents = call_args['triggered_agents']
    assert len(triggered_agents) == 2
    agent_names = [agent['agent_name'] for agent in triggered_agents]
    assert 'test_agent' in agent_names
    assert 'another_agent' in agent_names
    assert 'disabled_agent' not in agent_names


def test_process_events_with_recall_observation_extensions_disabled(
    agent_config, conversation_memory
):
    """Test processing a RecallObservation when prompt extensions are disabled."""
    # Modify the agent config to disable prompt extensions
    agent_config.enable_prompt_extensions = False

    obs = RecallObservation(
        recall_type=RecallType.ENVIRONMENT_INFO,
        repo_name='test-repo',
        repo_directory='/path/to/repo',
        content='Recalled environment info',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # When prompt extensions are disabled, the RecallObservation should be ignored
    assert len(messages) == 1  # Only the initial system message
    assert messages[0].role == 'system'

    # Verify the prompt_manager was not called
    conversation_memory.prompt_manager.build_additional_info.assert_not_called()
    conversation_memory.prompt_manager.build_microagent_info.assert_not_called()


def test_process_events_with_empty_microagent_knowledge(conversation_memory):
    """Test processing a RecallObservation with empty microagent knowledge."""
    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[],
        content='Recalled knowledge from microagents',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # The implementation returns an empty string but still creates a message
    assert len(messages) == 2
    assert messages[0].role == 'system'
    assert messages[1].role == 'user'
    assert len(messages[1].content) == 1
    assert isinstance(messages[1].content[0], TextContent)
    assert messages[1].content[0].text == ''

    # When there are no triggered agents, build_microagent_info is not called
    conversation_memory.prompt_manager.build_microagent_info.assert_not_called()


def test_process_events_with_recall_observation_deduplication(conversation_memory):
    """Test that RecallObservations are properly deduplicated based on agent_name."""
    # Create a sequence of RecallObservations with overlapping agents
    obs1 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            {
                'agent_name': 'python_agent',
                'trigger_word': 'python',
                'content': 'Python best practices v1',
            },
            {
                'agent_name': 'git_agent',
                'trigger_word': 'git',
                'content': 'Git best practices v1',
            },
            {
                'agent_name': 'image_agent',
                'trigger_word': 'image',
                'content': 'Image best practices v1',
            },
        ],
        content='First recall',
    )

    obs2 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            {
                'agent_name': 'python_agent',
                'trigger_word': 'python',
                'content': 'Python best practices v2',
            },
        ],
        content='Second recall',
    )

    obs3 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            {
                'agent_name': 'git_agent',
                'trigger_word': 'git',
                'content': 'Git best practices v3',
            },
        ],
        content='Third recall',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs1, obs2, obs3],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # Verify that only the most recent content for each agent is included
    assert len(messages) == 4  # system + 3 recalls
    recall_messages = messages[1:]  # Skip system message

    # First recall should only include image_agent (git_agent and python_agent appears later)
    assert 'Image best practices v1' in recall_messages[0].content[0].text
    assert 'Git best practices v1' not in recall_messages[0].content[0].text
    assert 'Python best practices v1' not in recall_messages[0].content[0].text

    # Second recall should include python_agent (it's the most recent for that agent)
    assert 'Python best practices v2' in recall_messages[1].content[0].text

    # Third recall should include git_agent (it's the most recent for that agent)
    assert 'Git best practices v3' in recall_messages[2].content[0].text


def test_process_events_with_recall_observation_deduplication_disabled_agents(
    conversation_memory,
):
    """Test that disabled agents are filtered out after deduplication."""
    # Create a sequence of RecallObservations with disabled agents
    obs1 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            {
                'agent_name': 'disabled_agent',
                'trigger_word': 'disabled',
                'content': 'Disabled agent content',
            },
            {
                'agent_name': 'enabled_agent',
                'trigger_word': 'enabled',
                'content': 'Enabled agent content v1',
            },
        ],
        content='First recall',
    )

    obs2 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[
            {
                'agent_name': 'enabled_agent',
                'trigger_word': 'enabled',
                'content': 'Enabled agent content v2',
            },
        ],
        content='Second recall',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs1, obs2],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # Verify that disabled agents are filtered out and only the most recent content for enabled agents is included
    assert len(messages) == 3  # system + 2 recalls
    recall_messages = messages[1:]  # Skip system message

    # First recall should not include disabled_agent
    assert 'Disabled agent content' not in recall_messages[0].content[0].text
    assert (
        'Enabled agent content v1' not in recall_messages[0].content[0].text
    )  # Because it appears later

    # Second recall should include enabled_agent (it's the most recent)
    assert 'Enabled agent content v2' in recall_messages[1].content[0].text


def test_process_events_with_recall_observation_deduplication_empty(
    conversation_memory,
):
    """Test that empty RecallObservations are handled correctly."""
    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE_MICROAGENT,
        microagent_knowledge=[],
        content='Empty recall',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # Verify that empty RecallObservations are handled gracefully
    assert len(messages) == 2  # system + empty recall
    assert messages[1].content[0].text == ''  # Empty string for empty recall
