from dataclasses import Field
from types import UnionType
from typing import Any, get_args, get_origin

from pydantic.fields import FieldInfo

OH_DEFAULT_AGENT = 'CodeActAgent'
OH_MAX_ITERATIONS = 500


def get_field_info(field: Field | FieldInfo) -> dict[str, Any]:
    """Extract information about a dataclass field: type, optional, and default.

    Args:
        field: The field to extract information from.

    Returns: A dict with the field's type, whether it's optional, and its default value.
    """
    field_type = field.type if isinstance(field, Field) else field.annotation
    optional = False

    # for types like str | None, find the non-None type and set optional to True
    # this is useful for the frontend to know if a field is optional
    # and to show the correct type in the UI
    # Note: this only works for UnionTypes with None as one of the types
    if get_origin(field_type) is UnionType:
        types = get_args(field_type)
        non_none_arg = next((t for t in types if t is not type(None)), None)
        if non_none_arg is not None:
            field_type = non_none_arg
            optional = True

    # type name in a pretty format
    type_name = (
        field_type.__name__ if hasattr(field_type, '__name__') else str(field_type)
    )

    # default is always present
    default = field.default

    # return a schema with the useful info for frontend
    return {'type': type_name.lower(), 'optional': optional, 'default': default}
