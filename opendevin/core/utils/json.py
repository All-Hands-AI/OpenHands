import json

from json_repair import repair_json

from opendevin.core.exceptions import LLMOutputError


def my_encoder(obj):
    """
    Encodes objects as dictionaries

    Parameters:
    - obj (Object): An object that will be converted

    Returns:
    - dict: If the object can be converted it is returned in dict format
    """
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()


def dumps(obj, **kwargs):
    """
    Serialize an object to str format
    """

    return json.dumps(obj, default=my_encoder, **kwargs)


def loads(json_str, **kwargs):
    """
    Create a JSON object from str
    """
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
