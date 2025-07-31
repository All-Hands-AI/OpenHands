import json
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


def _extract_content_from_event(event: dict) -> str | None:
    """Extract the main content from an event (similar to mem0 logic)."""
    content = event.get('message')
    if not content:
        args = event.get('args')
        if args and isinstance(args, dict):
            content = args.get('content')
    if not content:
        content = event.get('content')
    return content


def _extract_file_text_from_tool_call(tool_calls: list) -> str | None:
    """Extract file_text from tool call arguments (similar to mem0 logic)."""
    if tool_calls and 'function' in tool_calls[0]:
        arguments_str = tool_calls[0]['function'].get('arguments')
        if arguments_str:
            try:
                arguments_json = json.loads(arguments_str)
                return arguments_json.get('file_text') or arguments_str
            except Exception:
                return arguments_str
    return None


def _extract_from_edit_event(event_dict: dict) -> str | None:
    """Extract content from edit tool calls (str_replace_editor, etc.)."""
    tool_call_metadata = event_dict.get('tool_call_metadata', {})
    model_response = tool_call_metadata.get('model_response', {})
    choices = model_response.get('choices', [])

    if choices and 'message' in choices[0]:
        message_obj = choices[0]['message']
        tool_calls = message_obj.get('tool_calls', [])

        # Extract file_text from edit tool calls
        if tool_calls and 'function' in tool_calls[0]:
            arguments_str = tool_calls[0]['function'].get('arguments')
            if arguments_str:
                try:
                    arguments_json = json.loads(arguments_str)
                    file_text = arguments_json.get(
                        'file_text', ''
                    ) or arguments_json.get('new_str', '')

                    if file_text and len(file_text.strip()) > 10:
                        # Try to extract JSON from file content first
                        json_result = _try_extract_json(file_text)
                        if json_result:
                            result = json.dumps(json_result)
                            return result
                        else:
                            # Use the file content as final result
                            return file_text
                except json.JSONDecodeError:
                    pass
    return None


def _extract_from_finish_event(event_dict: dict) -> str | None:
    """Extract content from finish action tool calls."""
    tool_call_metadata = event_dict.get('tool_call_metadata', {})
    model_response = tool_call_metadata.get('model_response', {})
    choices = model_response.get('choices', [])

    if choices and 'message' in choices[0]:
        message_obj = choices[0]['message']
        tool_calls = message_obj.get('tool_calls', [])

        content = message_obj.get('content', '')
        if content and len(content.strip()) > 0:
            # Try to extract JSON first
            json_result = _try_extract_json(content)
            if json_result:
                result = json.dumps(json_result)
                return result

        # Extract the actual JSON from tool call arguments
        if tool_calls and 'function' in tool_calls[0]:
            arguments_str = tool_calls[0]['function'].get('arguments')
            if arguments_str:
                try:
                    arguments_json = json.loads(arguments_str)
                    # Extract the message field which contains the actual JSON result
                    message_content = arguments_json.get('message', '')

                    # Try to parse the message as JSON
                    try:
                        final_json = json.loads(message_content)
                        result = json.dumps(final_json)
                        return result
                    except json.JSONDecodeError:
                        return message_content
                except json.JSONDecodeError:
                    return arguments_str
    return None


def _extract_from_message_event(event_dict: dict) -> str | None:
    """Extract content from regular agent messages."""
    content = _extract_content_from_event(event_dict)
    if content and len(content.strip()) > 10:
        # Try to extract JSON first
        json_result = _try_extract_json(content)
        if json_result:
            result = json.dumps(json_result)
            return result
        else:
            return content
    return None


def _extract_from_read_event(event_dict: dict) -> str | None:
    """Extract content from read action/observation events for .md and .txt files only."""
    # Check if this is a read observation
    if event_dict.get('observation') != 'read':
        return None

    # Check file path from extras
    extras = event_dict.get('extras', {})
    path = extras.get('path', '')

    # Only process .md and .txt files, exclude coding files
    if not path or not isinstance(path, str):
        return None

    # Check file extension - only .md and .txt
    valid_extensions = ('.md', '.txt')
    if not any(path.lower().endswith(ext) for ext in valid_extensions):
        return None

    # Exclude common coding file patterns even if they have .md/.txt extension
    coding_patterns = [
        'README.md',
        'readme.md',
        'CHANGELOG.md',
        'changelog.md',
        'LICENSE.md',
        'license.md',
        'CONTRIBUTING.md',
        'contributing.md',
        'requirements.txt',
        'package.json',
        'setup.py',
        'Dockerfile',
    ]
    filename = path.split('/')[-1] if '/' in path else path
    if any(pattern.lower() in filename.lower() for pattern in coding_patterns):
        return None

    # Extract content
    content = event_dict.get('content', '')
    if not content or len(content.strip()) < 10:
        return None

    lines = content.split('\n')
    cleaned_lines = []
    start_processing = False

    for line in lines:
        line_stripped = line.strip()

        # Skip command description lines
        if any(
            keyword in line_stripped.lower()
            for keyword in [
                "here's the result of running",
                'result of running',
                'running `',
                'command:',
                'executing',
                'running command',
            ]
        ):
            continue

        # Skip empty lines at the beginning
        if not line_stripped and not start_processing:
            continue

        # Look for numbered lines (from cat -n output) or start of actual content
        if line_stripped and (
            line_stripped[0].isdigit()
            or start_processing
            or not line_stripped.startswith('     ')
        ):
            start_processing = True
            # Remove line numbers from cat -n output
            if '\t' in line and line_stripped[0].isdigit():
                parts = line.split('\t', 1)
                if len(parts) > 1:
                    cleaned_lines.append(parts[1])
            else:
                cleaned_lines.append(line)

    cleaned_content = '\n'.join(cleaned_lines).strip()

    if len(cleaned_content) > 20:
        return cleaned_content

    return None


def _try_extract_json(content: str) -> dict | None:
    """Try to extract JSON from content using various patterns."""
    if not content:
        return None

    import json
    import re

    json_patterns = [
        r'```json\s*\n?(.*?)\n?```',  # JSON in code blocks
        r'```\s*\n?(.*?)\n?```',  # General code blocks
        r'\{.*?\}',  # JSON objects (including nested)
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                clean_match = match.strip()
                if not clean_match.startswith('{'):
                    continue
                return json.loads(clean_match)
            except json.JSONDecodeError:
                continue
    return None
