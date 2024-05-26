import json
from datetime import datetime

from json_repair import repair_json

from opendevin.core.exceptions import LLMOutputError
from opendevin.events.event import Event
from opendevin.events.serialization import event_to_dict


def my_default_encoder(obj):
    """
    Custom JSON encoder that handles datetime and event objects
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Event):
        return event_to_dict(obj)
    return json.JSONEncoder().default(obj)


def dumps(obj, **kwargs):
    """
    Serialize an object to str format
    """

    return json.dumps(obj, default=my_default_encoder, **kwargs)


def loads(json_str, **kwargs):
    """
    Create a JSON object from str
    """
    try:
        return json.loads(json_str, **kwargs)
    except json.JSONDecodeError:
        pass
    depth = 0
    start = -1
    for i, char in enumerate(json_str):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                response = json_str[start : i + 1]
                try:
                    json_str = repair_json(response)
                    return json.loads(json_str, **kwargs)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    raise LLMOutputError(
                        'Invalid JSON in response. Please make sure the response is a valid JSON object.'
                    ) from e
    raise LLMOutputError('No valid JSON object found in response.')
