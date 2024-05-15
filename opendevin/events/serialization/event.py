from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

from .action import action_from_dict
from .observation import observation_from_dict
from .utils import remove_fields

if TYPE_CHECKING:
    from opendevin.events.event import Event

# TODO: move `content` into `extras`
TOP_KEYS = ['id', 'timestamp', 'source', 'message', 'cause', 'action', 'observation']

DELETE_FROM_MEMORY_EXTRAS = {
    'screenshot',
    'dom_object',
    'axtree_object',
    'open_pages_urls',
    'active_page_index',
    'last_browser_action',
    'focused_element_bid',
}


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if obj is None:
        return None
    return str(obj)


def event_from_dict(data) -> 'Event':
    if 'action' in data:
        return action_from_dict(data)
    elif 'observation' in data:
        return observation_from_dict(data)
    else:
        raise ValueError('Unknown event type: ' + data)


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
            d['timestamp'] = json_serial(d['timestamp'])
        props.pop(key, None)
    if 'action' in d:
        d['args'] = props
    elif 'observation' in d:
        d['content'] = props.pop('content', '')
        d['extras'] = props
    else:
        raise ValueError('Event must be either action or observation')
    return d


def event_to_memory(event: 'Event') -> dict:
    d = event_to_dict(event)
    d.pop('id', None)
    d.pop('cause', None)
    d.pop('timestamp', None)
    d.pop('message', None)
    if 'extras' in d:
        remove_fields(d['extras'], DELETE_FROM_MEMORY_EXTRAS)
    return d
