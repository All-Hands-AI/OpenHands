import json
from json_repair import repair_json
from typing import Any, cast


def my_encoder(obj: Any) -> dict[str, Any]:
    """
    Encodes objects as dictionaries

    Parameters:
    - obj (Object): An object that will be converted

    Returns:
    - dict: If the object can be converted it is returned in dict format
    """
    if hasattr(obj, 'to_dict'):
        return cast(dict[str, Any], obj.to_dict())
    return {}


def dumps(obj: Any, **kwargs: Any) -> str:
    """
    Serialize an object to str format
    """

    return json.dumps(obj, default=my_encoder, **kwargs)


def loads(s: str, **kwargs: Any) -> Any:
    """
    Create a JSON object from str
    """
    json_start = s.find('{')
    json_end = s.rfind('}') + 1
    if json_start == -1 or json_end == -1:
        raise ValueError('Invalid response: no JSON found')
    s = s[json_start:json_end]
    s = repair_json(s)
    return json.loads(s, **kwargs)
