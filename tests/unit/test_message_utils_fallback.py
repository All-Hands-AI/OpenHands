from openhands.core.message_utils import (
    get_token_usage_for_event,
    get_token_usage_for_event_id,
)
from openhands.events.event import Event
from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Metrics, TokenUsage


def test_get_token_usage_for_event_fallback():
    """
    Verify that if tool_call_metadata.model_response.id is missing or mismatched,
    but event.response_id is set to a valid usage ID, we find the usage record via fallback.
    """
    metrics = Metrics(model_name='fallback-test')
    usage_record = TokenUsage(
        model='fallback-test',
        prompt_tokens=22,
        completion_tokens=8,
        cache_read_tokens=3,
        cache_write_tokens=2,
        response_id='fallback-response-id',
    )
    metrics.add_token_usage(
        prompt_tokens=usage_record.prompt_tokens,
        completion_tokens=usage_record.completion_tokens,
        cache_read_tokens=usage_record.cache_read_tokens,
        cache_write_tokens=usage_record.cache_write_tokens,
        response_id=usage_record.response_id,
    )

    event = Event()
    # Provide some mismatched tool_call_metadata:
    event._tool_call_metadata = ToolCallMetadata(
        tool_call_id='irrelevant-tool-call',
        function_name='fake_function',
        model_response={'id': 'not-matching-any-usage'},
        total_calls_in_response=1,
    )
    # But also set event.response_id to the actual usage ID
    event._response_id = 'fallback-response-id'

    found = get_token_usage_for_event(event, metrics)
    assert found is not None
    assert found.prompt_tokens == 22
    assert found.response_id == 'fallback-response-id'


def test_get_token_usage_for_event_id_fallback():
    """
    Verify that get_token_usage_for_event_id also falls back to event.response_id
    if tool_call_metadata.model_response.id is missing or mismatched.
    """

    # NOTE: this should never happen (tm), but there is a hint in the code that it might:
    # message_utils.py: 166 ("(overwrites any previous message with the same response_id)")
    # so we'll handle it gracefully.
    metrics = Metrics(model_name='fallback-test')
    usage_record = TokenUsage(
        model='fallback-test',
        prompt_tokens=15,
        completion_tokens=4,
        cache_read_tokens=1,
        cache_write_tokens=0,
        response_id='resp-fallback',
    )
    metrics.token_usages.append(usage_record)

    events = []
    for i in range(3):
        e = Event()
        e._id = i
        if i == 1:
            # Mismatch in tool_call_metadata
            e._tool_call_metadata = ToolCallMetadata(
                tool_call_id='tool-123',
                function_name='whatever',
                model_response={'id': 'no-such-response'},
                total_calls_in_response=1,
            )
            # But the event's top-level response_id is correct
            e._response_id = 'resp-fallback'
        events.append(e)

    # Searching from event_id=2 goes back to event1, which has fallback response_id
    found_usage = get_token_usage_for_event_id(events, 2, metrics)
    assert found_usage is not None
    assert found_usage.response_id == 'resp-fallback'
    assert found_usage.prompt_tokens == 15