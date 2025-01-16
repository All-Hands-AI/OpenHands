from dataclasses import asdict
from datetime import datetime

from openhands.events import Event, EventSource
from openhands.events.observation.observation import Observation
from openhands.events.serialization.action import action_from_dict
from openhands.events.serialization.observation import observation_from_dict
from openhands.events.serialization.utils import remove_fields
from openhands.events.tool import ToolCallMetadata

# TODO: move `content` into `extras`
TOP_KEYS = [
    'id',
    'timestamp',
    'source',
    'message',
    'cause',
    'action',
    'observation',
    'tool_call_metadata',
]
UNDERSCORE_KEYS = ['id', 'timestamp', 'source', 'cause', 'tool_call_metadata']

DELETE_FROM_TRAJECTORY_EXTRAS = {
    'screenshot',
    'dom_object',
    'axtree_object',
    'active_page_index',
    'last_browser_action',
    'last_browser_action_error',
    'focused_element_bid',
    'extra_element_properties',
}

DELETE_FROM_MEMORY_EXTRAS = DELETE_FROM_TRAJECTORY_EXTRAS | {'open_pages_urls'}


def event_from_dict(data) -> 'Event':
    evt: Event
    if 'action' in data:
        evt = action_from_dict(data)
    elif 'observation' in data:
        evt = observation_from_dict(data)
    else:
        raise ValueError('Unknown event type: ' + data)
    for key in UNDERSCORE_KEYS:
        if key in data:
            value = data[key]
            if key == 'timestamp' and isinstance(value, datetime):
                value = value.isoformat()
            if key == 'source':
                value = EventSource(value)
            if key == 'tool_call_metadata':
                value = ToolCallMetadata(**value)
            setattr(evt, '_' + key, value)
    return evt


def event_to_dict(event: 'Event') -> dict:
    props = asdict(event)
    d = {}
    for key in TOP_KEYS:
        if hasattr(event, key) and getattr(event, key) is not None:
            d[key] = getattr(event, key)
        elif hasattr(event, f'_{key}') and getattr(event, f'_{key}') is not None:
            d[key] = getattr(event, f'_{key}')
        if key == 'id' and d.get('id') == -1:
            d.pop('id', None)
        if key == 'timestamp' and 'timestamp' in d:
            if isinstance(d['timestamp'], datetime):
                d['timestamp'] = d['timestamp'].isoformat()
        if key == 'source' and 'source' in d:
            d['source'] = d['source'].value
        if key == 'tool_call_metadata' and 'tool_call_metadata' in d:
            d['tool_call_metadata'] = d['tool_call_metadata'].model_dump()
        props.pop(key, None)
    if 'security_risk' in props and props['security_risk'] is None:
        props.pop('security_risk')
    if 'action' in d:
        d['args'] = props
        if event.timeout is not None:
            d['timeout'] = event.timeout
    elif 'observation' in d:
        d['content'] = props.pop('content', '')
        d['extras'] = props
        # Include success field for CmdOutputObservation
        if hasattr(event, 'success'):
            d['success'] = event.success
    else:
        raise ValueError('Event must be either action or observation')
    return d


def event_to_trajectory(event: 'Event') -> dict:
    d = event_to_dict(event)
    if 'extras' in d:
        remove_fields(d['extras'], DELETE_FROM_TRAJECTORY_EXTRAS)
    return d


def event_to_memory(event: 'Event', max_message_chars: int) -> dict:
    d = event_to_dict(event)
    d.pop('id', None)
    d.pop('cause', None)
    d.pop('timestamp', None)
    d.pop('message', None)
    d.pop('image_urls', None)

    # runnable actions have some extra fields used in the BE/FE, which should not be sent to the LLM
    if 'args' in d:
        d['args'].pop('blocking', None)
        d['args'].pop('keep_prompt', None)
        d['args'].pop('confirmation_state', None)

    if 'extras' in d:
        remove_fields(d['extras'], DELETE_FROM_MEMORY_EXTRAS)
    if isinstance(event, Observation) and 'content' in d:
        d['content'] = truncate_content(d['content'], max_message_chars)
    return d


def truncate_content(content: str, max_chars: int) -> str:
    """Truncate the middle of the observation content if it is too long."""
    if len(content) <= max_chars or max_chars == -1:
        return content

    # truncate the middle and include a message to the LLM about it
    half = max_chars // 2
    return (
        content[:half]
        + '\n[... Observation truncated due to length ...]\n'
        + content[-half:]
    )
