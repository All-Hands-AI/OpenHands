from unittest.mock import Mock

import pytest

from openhands.core.message import ImageContent, TextContent
from openhands.core.message_utils import (
    get_action_message,
    get_observation_message,
    get_token_usage_for_event,
    get_token_usage_for_event_id,
)
from openhands.events.action import (
    AgentFinishAction,
    CmdRunAction,
    MessageAction,
)
from openhands.events.event import Event, EventSource, FileEditSource, FileReadSource
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.events.observation.commands import (
    CmdOutputMetadata,
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.files import FileEditObservation, FileReadObservation
from openhands.events.observation.reject import UserRejectObservation
from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Metrics, TokenUsage


def test_cmd_output_observation_message():
    obs = CmdOutputObservation(
        command='echo hello',
        content='Command output',
        metadata=CmdOutputMetadata(
            exit_code=0,
            prefix='[THIS IS PREFIX]',
            suffix='[THIS IS SUFFIX]',
        ),
    )

    tool_call_id_to_message = {}
    results = get_observation_message(
        obs, tool_call_id_to_message=tool_call_id_to_message
    )
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Observed result of command executed by user:' in result.content[0].text
    assert '[Command finished with exit code 0]' in result.content[0].text
    assert '[THIS IS PREFIX]' in result.content[0].text
    assert '[THIS IS SUFFIX]' in result.content[0].text


def test_ipython_run_cell_observation_message():
    obs = IPythonRunCellObservation(
        code='plt.plot()',
        content='IPython output\n![image](data:image/png;base64,ABC123)',
    )

    results = get_observation_message(obs, tool_call_id_to_message={})
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


def test_agent_delegate_observation_message():
    obs = AgentDelegateObservation(
        content='Content', outputs={'content': 'Delegated agent output'}
    )

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Delegated agent output' in result.content[0].text


def test_error_observation_message():
    obs = ErrorObservation('Error message')

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Error message' in result.content[0].text
    assert 'Error occurred in processing last action' in result.content[0].text


def test_unknown_observation_message():
    obs = Mock()

    with pytest.raises(ValueError, match='Unknown observation type'):
        get_observation_message(obs, tool_call_id_to_message={})


def test_file_edit_observation_message():
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='old content',
        new_content='new content',
        content='diff content',
        impl_source=FileEditSource.LLM_BASED_EDIT,
    )

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Existing file /test/file.txt is edited with' in result.content[0].text


def test_file_read_observation_message():
    obs = FileReadObservation(
        path='/test/file.txt',
        content='File content',
        impl_source=FileReadSource.DEFAULT,
    )

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == 'File content'


def test_browser_output_observation_message():
    obs = BrowserOutputObservation(
        url='http://example.com',
        trigger_by_action='browse',
        screenshot='',
        content='Page loaded',
        error=False,
    )

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert '[Current URL: http://example.com]' in result.content[0].text


def test_user_reject_observation_message():
    obs = UserRejectObservation('Action rejected')

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Action rejected' in result.content[0].text
    assert '[Last action has been rejected by the user]' in result.content[0].text


def test_function_calling_observation_message():
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

    results = get_observation_message(obs, tool_call_id_to_message={})
    assert len(results) == 0  # No direct message when using function calling


def test_message_action_with_image():
    action = MessageAction(
        content='Message with image',
        image_urls=['http://example.com/image.jpg'],
    )
    action._source = EventSource.AGENT

    results = get_action_message(action, {}, vision_is_active=True)
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'assistant'
    assert len(result.content) == 2
    assert isinstance(result.content[0], TextContent)
    assert isinstance(result.content[1], ImageContent)
    assert result.content[0].text == 'Message with image'
    assert result.content[1].image_urls == ['http://example.com/image.jpg']


def test_user_cmd_action_message():
    action = CmdRunAction(command='ls -l')
    action._source = EventSource.USER

    results = get_action_message(action, {})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'user'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'User executed the command' in result.content[0].text
    assert 'ls -l' in result.content[0].text


def test_agent_finish_action_with_tool_metadata():
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

    results = get_action_message(action, {})
    assert len(results) == 1

    result = results[0]
    assert result is not None
    assert result.role == 'assistant'
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert 'Initial thought\nTask completed' in result.content[0].text


def test_get_token_usage_for_event():
    """Test that we get the single matching usage record (if any) based on the event's model_response.id."""
    metrics = Metrics(model_name='test-model')
    usage_record = TokenUsage(
        model='test-model',
        prompt_tokens=10,
        completion_tokens=5,
        cache_read_tokens=2,
        cache_write_tokens=1,
        response_id='test-response-id',
    )
    metrics.add_token_usage(
        prompt_tokens=usage_record.prompt_tokens,
        completion_tokens=usage_record.completion_tokens,
        cache_read_tokens=usage_record.cache_read_tokens,
        cache_write_tokens=usage_record.cache_write_tokens,
        response_id=usage_record.response_id,
    )

    # Create an event referencing that response_id
    event = Event()
    mock_tool_call_metadata = ToolCallMetadata(
        tool_call_id='test-tool-call',
        function_name='fake_function',
        model_response={'id': 'test-response-id'},
        total_calls_in_response=1,
    )
    event._tool_call_metadata = (
        mock_tool_call_metadata  # normally you'd do event.tool_call_metadata = ...
    )

    # We should find that usage record
    found = get_token_usage_for_event(event, metrics)
    assert found is not None
    assert found.prompt_tokens == 10
    assert found.response_id == 'test-response-id'

    # If we change the event's response ID, we won't find anything
    mock_tool_call_metadata.model_response.id = 'some-other-id'
    found2 = get_token_usage_for_event(event, metrics)
    assert found2 is None

    # If the event has no tool_call_metadata, also returns None
    event._tool_call_metadata = None
    found3 = get_token_usage_for_event(event, metrics)
    assert found3 is None


def test_get_token_usage_for_event_id():
    """
    Test that we search backward from the event with the given id,
    finding the first usage record that matches a response_id in that or previous events.
    """
    metrics = Metrics(model_name='test-model')
    usage_1 = TokenUsage(
        model='test-model',
        prompt_tokens=12,
        completion_tokens=3,
        cache_read_tokens=2,
        cache_write_tokens=5,
        response_id='resp-1',
    )
    usage_2 = TokenUsage(
        model='test-model',
        prompt_tokens=7,
        completion_tokens=2,
        cache_read_tokens=1,
        cache_write_tokens=3,
        response_id='resp-2',
    )
    metrics._token_usages.append(usage_1)
    metrics._token_usages.append(usage_2)

    # Build a list of events
    events = []
    for i in range(5):
        e = Event()
        e._id = i
        # We'll attach usage_1 to event 1, usage_2 to event 3
        if i == 1:
            e._tool_call_metadata = ToolCallMetadata(
                tool_call_id='tid1',
                function_name='fn1',
                model_response={'id': 'resp-1'},
                total_calls_in_response=1,
            )
        elif i == 3:
            e._tool_call_metadata = ToolCallMetadata(
                tool_call_id='tid2',
                function_name='fn2',
                model_response={'id': 'resp-2'},
                total_calls_in_response=1,
            )
        events.append(e)

    # If we ask for event_id=3, we find usage_2 immediately
    found_3 = get_token_usage_for_event_id(events, 3, metrics)
    assert found_3 is not None
    assert found_3.response_id == 'resp-2'

    # If we ask for event_id=2, no usage in event2, so we check event1 -> usage_1 found
    found_2 = get_token_usage_for_event_id(events, 2, metrics)
    assert found_2 is not None
    assert found_2.response_id == 'resp-1'

    # If we ask for event_id=0, no usage in event0 or earlier, so return None
    found_0 = get_token_usage_for_event_id(events, 0, metrics)
    assert found_0 is None
