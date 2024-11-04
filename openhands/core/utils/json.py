import json
from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

from json_repair import repair_json
from litellm.types.utils import ModelResponse

from openhands.core.exceptions import LLMResponseError
from openhands.events.event import Event
from openhands.events.serialization import event_to_dict
from openhands.llm.metrics import Metrics


T = TypeVar('T')


def json_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for JSON operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except json.JSONDecodeError:
                if operation_name == "loads":
                    # Special handling for loads operation
                    return handle_malformed_json(args[0], **kwargs)
                raise LLMResponseError('Invalid JSON in response')
            except (ValueError, TypeError) as e:
                raise LLMResponseError(
                    'Invalid JSON in response. Please make sure the response is a valid JSON object.'
                ) from e
        return wrapper
    return decorator


def handle_malformed_json(json_str: str, **kwargs) -> Any:
    """Handle malformed JSON by attempting to extract and repair a JSON object"""
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
                    raise LLMResponseError(
                        'Invalid JSON in response. Please make sure the response is a valid JSON object.'
                    ) from e
    raise LLMResponseError('No valid JSON object found in response.')


def my_default_encoder(obj):
    """Custom JSON encoder that handles datetime and event objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Event):
        return event_to_dict(obj)
    if isinstance(obj, Metrics):
        return obj.get()
    if isinstance(obj, ModelResponse):
        return obj.model_dump()
    return json.JSONEncoder().default(obj)


@json_operation("dumps")
def dumps(obj, **kwargs):
    """Serialize an object to str format"""
    return json.dumps(obj, default=my_default_encoder, **kwargs)


@json_operation("loads")
def loads(json_str, **kwargs):
    """Create a JSON object from str"""
    return json.loads(json_str, **kwargs)

