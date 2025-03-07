from openhands.core.message_utils import (
    get_token_usage_for_event,
    get_token_usage_for_event_id,
)
from openhands.events.event import Event
from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Metrics, TokenUsage


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
