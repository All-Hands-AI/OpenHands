from unittest.mock import MagicMock, Mock

import pytest

from openhands.controller.state.state import State
from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import Event, EventSource, FileEditSource, FileReadSource
from openhands.events.observation import CmdOutputObservation
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
from openhands.utils.prompt import PromptManager


@pytest.fixture
def conversation_memory():
    prompt_manager = MagicMock(spec=PromptManager)
    prompt_manager.get_system_message.return_value = 'System message'
    return ConversationMemory(prompt_manager)


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
