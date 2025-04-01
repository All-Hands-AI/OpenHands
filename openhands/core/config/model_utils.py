from types import UnionType
from typing import Any, get_args, get_origin
from pydantic import BaseModel
from pydantic.fields import FieldInfo

def model_defaults_to_dict(model: BaseModel) -> dict[str, Any]:
    """Serialize field information in a dict for the frontend"""
    from openhands.core.config.config_utils import get_field_info
    result = {}
    for name, field in model.model_fields.items():
        field_value = getattr(model, name)
        if isinstance(field_value, BaseModel):
            result[name] = model_defaults_to_dict(field_value)
        else:
            result[name] = get_field_info(field)
    return result