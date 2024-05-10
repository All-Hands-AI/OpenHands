from dataclasses import asdict
from typing import TYPE_CHECKING

from .action import action_from_dict
from .observation import observation_from_dict

if TYPE_CHECKING:
    from opendevin.events.event import Event

# TODO: move `content` into `extras`
TOP_KEYS = ['id', 'timestamp', 'source', 'message', 'action', 'observation', 'content']


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
        if hasattr(event, key):
            d[key] = getattr(event, key)
        elif hasattr(event, f'_{key}'):
            d[key] = getattr(event, f'_{key}')
        props.pop(key, None)
    if 'action' in d:
        d['args'] = props
    elif 'observation' in d:
        d['extras'] = props
    else:
        raise ValueError('Event must be either action or observation')
    return d
