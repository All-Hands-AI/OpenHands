from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.events import Event, EventSource
from openhands.events.serialization.action import action_from_dict
from openhands.events.serialization.observation import observation_from_dict
from openhands.events.serialization.utils import remove_fields
from openhands.events.tool import ToolCallMetadata
from openhands.llm.metrics import Cost, Metrics, ResponseLatency, TokenUsage

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
    'llm_metrics',
]
UNDERSCORE_KEYS = [
    'id',
    'timestamp',
    'source',
    'cause',
    'tool_call_metadata',
    'llm_metrics',
]

DELETE_FROM_TRAJECTORY_EXTRAS = {
    'dom_object',
    'axtree_object',
    'active_page_index',
    'last_browser_action',
    'last_browser_action_error',
    'focused_element_bid',
    'extra_element_properties',
}

DELETE_FROM_TRAJECTORY_EXTRAS_AND_SCREENSHOTS = DELETE_FROM_TRAJECTORY_EXTRAS | {
    'screenshot',
    'set_of_marks',
}


def _convert_dict_to_pydantic(
    data: dict | Any, model_class: type[BaseModel]
) -> BaseModel:
    """Convert a dictionary to a Pydantic model, handling nested dictionaries recursively."""
    if not isinstance(data, dict):
        return data

    for key, value in data.items():
        if isinstance(value, dict):
            # Try to find the corresponding field type in the model
            field = model_class.model_fields.get(key)
            if (
                field
                and hasattr(field.annotation, '__origin__')
                and issubclass(field.annotation.__origin__, BaseModel)
            ):
                data[key] = _convert_dict_to_pydantic(
                    value, field.annotation.__origin__
                )
            elif (
                field
                and isinstance(field.annotation, type)
                and issubclass(field.annotation, BaseModel)
            ):
                data[key] = _convert_dict_to_pydantic(value, field.annotation)
        elif isinstance(value, list):
            data[key] = [
                _convert_dict_to_pydantic(item, model_class)
                if isinstance(item, dict)
                else item
                for item in value
            ]

    return model_class(**data)


def event_from_dict(data: dict[str, Any]) -> 'Event':
    evt: Event
    if 'action' in data:
        evt = action_from_dict(data)
    elif 'observation' in data:
        evt = observation_from_dict(data)
    else:
        raise ValueError(f'Unknown event type: {data}')

    for key in UNDERSCORE_KEYS:
        if key in data:
            value = data[key]
            if key == 'timestamp' and isinstance(value, datetime):
                value = value.isoformat()
            if key == 'source':
                value = EventSource(value)
            if key == 'tool_call_metadata':
                value = ToolCallMetadata(**value)
            if key == 'llm_metrics':
                metrics = Metrics()
                if isinstance(value, dict):
                    metrics.accumulated_cost = value.get('accumulated_cost', 0.0)
                    for cost in value.get('costs', []):
                        metrics._costs.append(Cost(**cost))
                    metrics.response_latencies = [
                        ResponseLatency(**latency)
                        for latency in value.get('response_latencies', [])
                    ]
                    metrics.token_usages = [
                        TokenUsage(**usage) for usage in value.get('token_usages', [])
                    ]
                    if 'accumulated_token_usage' in value:
                        metrics._accumulated_token_usage = TokenUsage(
                            **value.get('accumulated_token_usage', {})
                        )
                value = metrics
            setattr(evt, '_' + key, value)

    # Handle nested BaseModel objects in the event's properties
    if hasattr(evt, 'nested') and isinstance(evt.nested, dict):
        # Try to find the corresponding model class from the event's type hints
        from typing import get_type_hints

        type_hints = get_type_hints(type(evt))
        if (
            'nested' in type_hints
            and isinstance(type_hints['nested'], type)
            and issubclass(type_hints['nested'], BaseModel)
        ):
            evt.nested = _convert_dict_to_pydantic(evt.nested, type_hints['nested'])

    return evt


def _convert_pydantic_to_dict(obj: BaseModel | dict | list | Any) -> dict | list | Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: _convert_pydantic_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_pydantic_to_dict(item) for item in obj]
    return obj


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
        if key == 'recall_type' and 'recall_type' in d:
            d['recall_type'] = d['recall_type'].value
        if key == 'tool_call_metadata' and 'tool_call_metadata' in d:
            d['tool_call_metadata'] = d['tool_call_metadata'].model_dump()
        if key == 'llm_metrics' and 'llm_metrics' in d:
            d['llm_metrics'] = d['llm_metrics'].get()
        props.pop(key, None)
    if 'security_risk' in props and props['security_risk'] is None:
        props.pop('security_risk')
    if 'action' in d:
        d['args'] = props
        if event.timeout is not None:
            d['timeout'] = event.timeout
    elif 'observation' in d:
        d['content'] = props.pop('content', '')

        # props is a dict whose values can include a complex object like an instance of a BaseModel subclass
        # such as CmdOutputMetadata
        # we serialize it along with the rest
        # we also handle the Enum conversion for RecallObservation
        d['extras'] = {
            k: (v.value if isinstance(v, Enum) else _convert_pydantic_to_dict(v))
            for k, v in props.items()
        }
        logger.debug(f'extras data in event_to_dict: {d["extras"]}')
        # Include success field for CmdOutputObservation
        if hasattr(event, 'success'):
            d['success'] = event.success
    else:
        raise ValueError(f'Event must be either action or observation. has: {event}')
    return d


def event_to_trajectory(event: 'Event', include_screenshots: bool = False) -> dict:
    d = event_to_dict(event)
    if 'extras' in d:
        remove_fields(
            d['extras'],
            DELETE_FROM_TRAJECTORY_EXTRAS
            if include_screenshots
            else DELETE_FROM_TRAJECTORY_EXTRAS_AND_SCREENSHOTS,
        )
    return d


def truncate_content(content: str, max_chars: int | None = None) -> str:
    """Truncate the middle of the observation content if it is too long."""
    if max_chars is None or len(content) <= max_chars or max_chars < 0:
        return content

    # truncate the middle and include a message to the LLM about it
    half = max_chars // 2
    return (
        content[:half]
        + '\n[... Observation truncated due to length ...]\n'
        + content[-half:]
    )
