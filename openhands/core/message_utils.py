from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.llm.metrics import Metrics, TokenUsage


def get_token_usage_for_event(event: Event, metrics: Metrics) -> TokenUsage | None:
    """Returns at most one token usage record by checking in order:
      - event.response_id, if set
      - tool_call_metadata.model_response.id, if present

    If neither exist or none matches in metrics.token_usages, returns None.
    """
    # 1) Check event.response_id first
    if event.response_id:
        return next(
            (u for u in metrics.token_usages if u.response_id == event.response_id),
            None,
        )

    # 2) Fallback to tool_call_metadata's response.id if present
    if event.tool_call_metadata and event.tool_call_metadata.model_response:
        tool_response_id = event.tool_call_metadata.model_response.get('id')
        if tool_response_id:
            return next(
                (u for u in metrics.token_usages if u.response_id == tool_response_id),
                None,
            )

    return None


def estimate_token_usage_at_event_id(
    events: list[Event], metrics: Metrics, event_id: int = -1
) -> TokenUsage | None:
    """Starting from the event with .id == event_id and moving backwards in `events`,
    find the first TokenUsage record (if any) associated either with:
      - event.response_id, or
      - tool_call_metadata.model_response.id
    Returns the first match found, or None if none is found.
    """
    if event_id == -1:
        event_id = events[-1].id

    # Find the index of the event with the given id
    idx = next((i for i, e in enumerate(events) if e.id == event_id), None)
    if idx is None:
        return None

    # Search backward from idx down to 0
    for i in range(idx, -1, -1):
        usage = get_token_usage_for_event(events[i], metrics)
        if usage is not None:
            return usage
    return None


def exceeds_token_limit(events: list[Event], metrics: Metrics, max_tokens: int) -> bool:
    """
    Checks if the token usage for the given event exceeds the specified maximum token limit.

    Args:
        event: The event to check token usage for
        metrics: The metrics containing token usage records
        max_tokens: The maximum token limit to compare against

    Returns:
        bool: True if the event's token usage exceeds the limit, False otherwise
        (also returns False if no token usage record is found)
    """
    usage = estimate_token_usage_at_event_id(events, metrics)
    if usage is None or not usage.prompt_tokens:
        return False

    logger.debug(f'Usage: {usage}')
    logger.debug(
        f'Comparing {usage.prompt_tokens + usage.completion_tokens} > {max_tokens}'
    )
    # Compare against prompt tokens (input tokens) + completion tokens (output tokens)
    return usage.prompt_tokens + usage.completion_tokens > max_tokens
