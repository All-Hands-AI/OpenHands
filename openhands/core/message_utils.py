from openhands.events.event import Event
from openhands.llm.metrics import Metrics, TokenUsage


def get_token_usage_for_event(event: Event, metrics: Metrics) -> TokenUsage | None:
    """
    Returns at most one token usage record for the `model_response.id` in this event's
    `tool_call_metadata`.

    If no response_id is found, or none match in metrics.token_usages, returns None.
    """
    if event.tool_call_metadata and event.tool_call_metadata.model_response:
        response_id = event.tool_call_metadata.model_response.get('id')
        if response_id:
            return next(
                (
                    usage
                    for usage in metrics.token_usages
                    if usage.response_id == response_id
                ),
                None,
            )
    return None


def get_token_usage_for_event_id(
    events: list[Event], event_id: int, metrics: Metrics
) -> TokenUsage | None:
    """
    Starting from the event with .id == event_id and moving backwards in `events`,
    find the first TokenUsage record (if any) associated with a response_id from
    tool_call_metadata.model_response.id.

    Returns the first match found, or None if none is found.
    """
    # find the index of the event with the given id
    idx = next((i for i, e in enumerate(events) if e.id == event_id), None)
    if idx is None:
        return None

    # search backward from idx down to 0
    for i in range(idx, -1, -1):
        usage = get_token_usage_for_event(events[i], metrics)
        if usage is not None:
            return usage
    return None
