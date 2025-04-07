import os
import shutil
from unittest.mock import MagicMock, Mock

import pytest
from litellm import ChatCompletionMessageToolCall

from openhands.controller.state.state import State
from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import (
    Event,
    EventSource,
    FileEditSource,
    FileReadSource,
    RecallType,
)
from openhands.events.observation import CmdOutputObservation
from openhands.events.observation.agent import (
    MicroagentKnowledge,
    RecallObservation,
)
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
    prompt_manager.build_workspace_context.return_value = (
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
def prompt_dir(tmp_path):
    # Copy contents from "openhands/agenthub/codeact_agent" to the temp directory
    shutil.copytree(
        'openhands/agenthub/codeact_agent/prompts', tmp_path, dirs_exist_ok=True
    )

    # Return the temporary directory path
    return tmp_path


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


def test_process_events_with_empty_environment_info(conversation_memory):
    """Test that empty environment info observations return an empty list of messages without calling build_workspace_context."""
    # Create a RecallObservation with empty info

    empty_obs = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='',
        repo_directory='',
        repo_instructions='',
        runtime_hosts={},
        additional_agent_instructions='',
        microagent_knowledge=[],
        content='Retrieved environment info',
    )

    initial_messages = [
        Message(role='system', content=[TextContent(text='System message')])
    ]

    messages = conversation_memory.process_events(
        condensed_history=[empty_obs],
        initial_messages=initial_messages,
        max_message_chars=None,
        vision_is_active=False,
    )

    # Should only contain the initial system message
    assert len(messages) == 1
    assert messages[0].role == 'system'

    # Verify that build_workspace_context was NOT called since all input values were empty
    conversation_memory.prompt_manager.build_workspace_context.assert_not_called()


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


def test_process_events_with_environment_microagent_observation(conversation_memory):
    """Test processing a RecallObservation with ENVIRONMENT info type."""
    obs = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test-repo',
        repo_directory='/path/to/repo',
        repo_instructions='# Test Repository\nThis is a test repository.',
        runtime_hosts={'localhost': 8080},
        content='Retrieved environment info',
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
    conversation_memory.prompt_manager.build_workspace_context.assert_called_once()
    call_args = conversation_memory.prompt_manager.build_workspace_context.call_args[1]
    assert isinstance(call_args['repository_info'], RepositoryInfo)
    assert call_args['repository_info'].repo_name == 'test-repo'
    assert call_args['repository_info'].repo_directory == '/path/to/repo'
    assert isinstance(call_args['runtime_info'], RuntimeInfo)
    assert call_args['runtime_info'].available_hosts == {'localhost': 8080}
    assert (
        call_args['repo_instructions']
        == '# Test Repository\nThis is a test repository.'
    )


def test_process_events_with_knowledge_microagent_microagent_observation(
    conversation_memory,
):
    """Test processing a RecallObservation with KNOWLEDGE type."""
    microagent_knowledge = [
        MicroagentKnowledge(
            name='test_agent',
            trigger='test',
            content='This is test agent content',
        ),
        MicroagentKnowledge(
            name='another_agent',
            trigger='another',
            content='This is another agent content',
        ),
        MicroagentKnowledge(
            name='disabled_agent',
            trigger='disabled',
            content='This is disabled agent content',
        ),
    ]

    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=microagent_knowledge,
        content='Retrieved knowledge from microagents',
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
    agent_names = [agent.name for agent in triggered_agents]
    assert 'test_agent' in agent_names
    assert 'another_agent' in agent_names
    assert 'disabled_agent' not in agent_names


def test_process_events_with_microagent_observation_extensions_disabled(
    agent_config, conversation_memory
):
    """Test processing a RecallObservation when prompt extensions are disabled."""
    # Modify the agent config to disable prompt extensions
    agent_config.enable_prompt_extensions = False

    obs = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='test-repo',
        repo_directory='/path/to/repo',
        content='Retrieved environment info',
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
    conversation_memory.prompt_manager.build_workspace_context.assert_not_called()
    conversation_memory.prompt_manager.build_microagent_info.assert_not_called()


def test_process_events_with_empty_microagent_knowledge(conversation_memory):
    """Test processing a RecallObservation with empty microagent knowledge."""
    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[],
        content='Retrieved knowledge from microagents',
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

    # The implementation returns an empty string and it doesn't creates a message
    assert len(messages) == 1
    assert messages[0].role == 'system'

    # When there are no triggered agents, build_microagent_info is not called
    conversation_memory.prompt_manager.build_microagent_info.assert_not_called()


def test_conversation_memory_processes_microagent_observation(prompt_dir):
    """Test that ConversationMemory processes RecallObservations correctly."""
    # Create a microagent_info.j2 template file
    template_path = os.path.join(prompt_dir, 'microagent_info.j2')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("""{% for agent_info in triggered_agents %}
<EXTRA_INFO>
The following information has been included based on a keyword match for "{{ agent_info.trigger_word }}".
It may or may not be relevant to the user's request.

    # Verify the template was correctly rendered
{{ agent_info.content }}
</EXTRA_INFO>
{% endfor %}
""")

    # Create a mock agent config
    agent_config = MagicMock(spec=AgentConfig)
    agent_config.enable_prompt_extensions = True
    agent_config.disabled_microagents = []

    # Create a PromptManager
    prompt_manager = PromptManager(prompt_dir=prompt_dir)

    # Initialize ConversationMemory
    conversation_memory = ConversationMemory(
        config=agent_config, prompt_manager=prompt_manager
    )

    # Create a RecallObservation with microagent knowledge
    microagent_observation = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='test_agent',
                trigger='test_trigger',
                content='This is triggered content for testing.',
            )
        ],
        content='Retrieved knowledge from microagents',
    )

    # Process the observation
    messages = conversation_memory._process_observation(
        obs=microagent_observation, tool_call_id_to_message={}, max_message_chars=None
    )

    # Verify the message was created correctly
    assert len(messages) == 1
    message = messages[0]
    assert message.role == 'user'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    expected_text = """<EXTRA_INFO>
The following information has been included based on a keyword match for "test_trigger".
It may or may not be relevant to the user's request.

This is triggered content for testing.
</EXTRA_INFO>"""

    assert message.content[0].text.strip() == expected_text.strip()

    # Clean up
    os.remove(os.path.join(prompt_dir, 'microagent_info.j2'))


def test_conversation_memory_processes_environment_microagent_observation(prompt_dir):
    """Test that ConversationMemory processes environment info RecallObservations correctly."""
    # Create an additional_info.j2 template file
    template_path = os.path.join(prompt_dir, 'additional_info.j2')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            f.write("""
{% if repository_info %}
<REPOSITORY_INFO>
At the user's request, repository {{ repository_info.repo_name }} has been cloned to directory {{ repository_info.repo_directory }}.
</REPOSITORY_INFO>
{% endif %}

{% if repository_instructions %}
<REPOSITORY_INSTRUCTIONS>
{{ repository_instructions }}
</REPOSITORY_INSTRUCTIONS>
{% endif %}

{% if runtime_info and runtime_info.available_hosts %}
<RUNTIME_INFORMATION>
The user has access to the following hosts for accessing a web application,
each of which has a corresponding port:
{% for host, port in runtime_info.available_hosts.items() %}
* {{ host }} (port {{ port }})
{% endfor %}
</RUNTIME_INFORMATION>
{% endif %}
""")

    # Create a mock agent config
    agent_config = MagicMock(spec=AgentConfig)
    agent_config.enable_prompt_extensions = True

    # Create a PromptManager
    prompt_manager = PromptManager(prompt_dir=prompt_dir)

    # Initialize ConversationMemory
    conversation_memory = ConversationMemory(
        config=agent_config, prompt_manager=prompt_manager
    )

    # Create a RecallObservation with environment info
    microagent_observation = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        repo_name='owner/repo',
        repo_directory='/workspace/repo',
        repo_instructions='This repository contains important code.',
        runtime_hosts={'example.com': 8080},
        content='Retrieved environment info',
    )

    # Process the observation
    messages = conversation_memory._process_observation(
        obs=microagent_observation, tool_call_id_to_message={}, max_message_chars=None
    )

    # Verify the message was created correctly
    assert len(messages) == 1
    message = messages[0]
    assert message.role == 'user'
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)

    # Check that the message contains the repository info
    assert '<REPOSITORY_INFO>' in message.content[0].text
    assert 'owner/repo' in message.content[0].text
    assert '/workspace/repo' in message.content[0].text

    # Check that the message contains the repository instructions
    assert '<REPOSITORY_INSTRUCTIONS>' in message.content[0].text
    assert 'This repository contains important code.' in message.content[0].text

    # Check that the message contains the runtime info
    assert '<RUNTIME_INFORMATION>' in message.content[0].text
    assert 'example.com (port 8080)' in message.content[0].text


def test_process_events_with_microagent_observation_deduplication(conversation_memory):
    """Test that RecallObservations are properly deduplicated based on agent name.

    The deduplication logic should keep the FIRST occurrence of each microagent
    and filter out later occurrences to avoid redundant information.
    """
    # Create a sequence of RecallObservations with overlapping agents
    obs1 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='python_agent',
                trigger='python',
                content='Python best practices v1',
            ),
            MicroagentKnowledge(
                name='git_agent',
                trigger='git',
                content='Git best practices v1',
            ),
            MicroagentKnowledge(
                name='image_agent',
                trigger='image',
                content='Image best practices v1',
            ),
        ],
        content='First retrieval',
    )

    obs2 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='python_agent',
                trigger='python',
                content='Python best practices v2',
            ),
        ],
        content='Second retrieval',
    )

    obs3 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='git_agent',
                trigger='git',
                content='Git best practices v3',
            ),
        ],
        content='Third retrieval',
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

    # Verify that only the first occurrence of content for each agent is included
    assert (
        len(messages) == 2
    )  # system + 1 microagent, because the second and third microagents are duplicates
    microagent_messages = messages[1:]  # Skip system message

    # First microagent should include all agents since they appear here first
    assert 'Image best practices v1' in microagent_messages[0].content[0].text
    assert 'Git best practices v1' in microagent_messages[0].content[0].text
    assert 'Python best practices v1' in microagent_messages[0].content[0].text


def test_process_events_with_microagent_observation_deduplication_disabled_agents(
    conversation_memory,
):
    """Test that disabled agents are filtered out and deduplication keeps the first occurrence."""
    # Create a sequence of RecallObservations with disabled agents
    obs1 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='disabled_agent',
                trigger='disabled',
                content='Disabled agent content',
            ),
            MicroagentKnowledge(
                name='enabled_agent',
                trigger='enabled',
                content='Enabled agent content v1',
            ),
        ],
        content='First retrieval',
    )

    obs2 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='enabled_agent',
                trigger='enabled',
                content='Enabled agent content v2',
            ),
        ],
        content='Second retrieval',
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

    # Verify that disabled agents are filtered out and only the first occurrence of enabled agents is included
    assert (
        len(messages) == 2
    )  # system + 1 microagent, the second is the same "enabled_agent"
    microagent_messages = messages[1:]  # Skip system message

    # First microagent should include enabled_agent but not disabled_agent
    assert 'Disabled agent content' not in microagent_messages[0].content[0].text
    assert 'Enabled agent content v1' in microagent_messages[0].content[0].text


def test_process_events_with_microagent_observation_deduplication_empty(
    conversation_memory,
):
    """Test that empty RecallObservations are handled correctly."""
    obs = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[],
        content='Empty retrieval',
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
    assert (
        len(messages) == 1
    )  # system message, because an empty microagent is not added to Messages


def test_has_agent_in_earlier_events(conversation_memory):
    """Test the _has_agent_in_earlier_events helper method."""
    # Create test RecallObservations
    obs1 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='agent1',
                trigger='trigger1',
                content='Content 1',
            ),
        ],
        content='First retrieval',
    )

    obs2 = RecallObservation(
        recall_type=RecallType.KNOWLEDGE,
        microagent_knowledge=[
            MicroagentKnowledge(
                name='agent2',
                trigger='trigger2',
                content='Content 2',
            ),
        ],
        content='Second retrieval',
    )

    obs3 = RecallObservation(
        recall_type=RecallType.WORKSPACE_CONTEXT,
        content='Environment info',
    )

    # Create a list with mixed event types
    events = [obs1, MessageAction(content='User message'), obs2, obs3]

    # Test looking for existing agents
    assert conversation_memory._has_agent_in_earlier_events('agent1', 2, events) is True
    assert conversation_memory._has_agent_in_earlier_events('agent1', 3, events) is True
    assert conversation_memory._has_agent_in_earlier_events('agent1', 4, events) is True

    # Test looking for an agent in a later position (should not find it)
    assert (
        conversation_memory._has_agent_in_earlier_events('agent2', 0, events) is False
    )
    assert (
        conversation_memory._has_agent_in_earlier_events('agent2', 1, events) is False
    )

    # Test looking for an agent in a different microagent type (should not find it)
    assert (
        conversation_memory._has_agent_in_earlier_events('non_existent', 3, events)
        is False
    )


class TestFilterUnmatchedToolCalls:
    @pytest.fixture
    def processor(self):
        return ConversationMemory()

    def test_empty_is_unchanged(self):
        assert list(ConversationMemory._filter_unmatched_tool_calls([])) == []

    def test_no_tool_calls_is_unchanged(self):
        messages = [
            Message(role='user', content=[TextContent(text='Hello')]),
            Message(role='assistant', content=[TextContent(text='Hi there')]),
            Message(role='user', content=[TextContent(text='How are you?')]),
        ]
        assert (
            list(ConversationMemory._filter_unmatched_tool_calls(messages)) == messages
        )

    def test_matched_tool_calls_are_unchanged(self):
        messages = [
            Message(role='user', content=[TextContent(text="What's the weather?")]),
            Message(
                role='assistant',
                content=[],
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id='call_1',
                        type='function',
                        function={'name': 'get_weather', 'arguments': ''},
                    )
                ],
            ),
            Message(
                role='tool',
                tool_call_id='call_1',
                content=[TextContent(text='Sunny, 75°F')],
            ),
            Message(role='assistant', content=[TextContent(text="It's sunny today.")]),
        ]

        # All tool calls have matching responses, should remain unchanged
        assert (
            list(ConversationMemory._filter_unmatched_tool_calls(messages)) == messages
        )

    def test_tool_call_without_response_is_removed(self):
        messages = [
            Message(role='user', content=[TextContent(text='Query')]),
            Message(
                role='tool',
                tool_call_id='missing_call',
                content=[TextContent(text='Response')],
            ),
            Message(role='assistant', content=[TextContent(text='Answer')]),
        ]

        expected_after_filter = [
            Message(role='user', content=[TextContent(text='Query')]),
            Message(role='assistant', content=[TextContent(text='Answer')]),
        ]

        result = list(ConversationMemory._filter_unmatched_tool_calls(messages))
        assert result == expected_after_filter

    def test_tool_response_without_call_is_removed(self):
        messages = [
            Message(role='user', content=[TextContent(text='Query')]),
            Message(
                role='assistant',
                content=[],
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id='unmatched_call',
                        type='function',
                        function={'name': 'some_function', 'arguments': ''},
                    )
                ],
            ),
            Message(role='assistant', content=[TextContent(text='Answer')]),
        ]

        expected_after_filter = [
            Message(role='user', content=[TextContent(text='Query')]),
            Message(role='assistant', content=[TextContent(text='Answer')]),
        ]

        result = list(ConversationMemory._filter_unmatched_tool_calls(messages))
        assert result == expected_after_filter

    def test_partial_matched_tool_calls_retains_matched(self):
        """When there are both matched and unmatched tools calls in a message, retain the message and only matched calls"""
        messages = [
            Message(role='user', content=[TextContent(text='Get data')]),
            Message(
                role='assistant',
                content=[],
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id='matched_call',
                        type='function',
                        function={'name': 'function1', 'arguments': ''},
                    ),
                    ChatCompletionMessageToolCall(
                        id='unmatched_call',
                        type='function',
                        function={'name': 'function2', 'arguments': ''},
                    ),
                ],
            ),
            Message(
                role='tool',
                tool_call_id='matched_call',
                content=[TextContent(text='Data')],
            ),
            Message(role='assistant', content=[TextContent(text='Result')]),
        ]

        expected = [
            Message(role='user', content=[TextContent(text='Get data')]),
            # This message should be modified to only include the matched tool call
            Message(
                role='assistant',
                content=[],
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id='matched_call',
                        type='function',
                        function={'name': 'function1', 'arguments': ''},
                    )
                ],
            ),
            Message(
                role='tool',
                tool_call_id='matched_call',
                content=[TextContent(text='Data')],
            ),
            Message(role='assistant', content=[TextContent(text='Result')]),
        ]

        result = list(ConversationMemory._filter_unmatched_tool_calls(messages))

        # Verify result structure
        assert len(result) == len(expected)
        for i, msg in enumerate(result):
            assert msg == expected[i]
