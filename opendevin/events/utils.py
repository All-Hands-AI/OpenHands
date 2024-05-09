def remove_fields(obj, fields: set[str]):
    """
    Remove fields from an object.

    Parameters:
    - obj: The dictionary, or list of dictionaries to remove fields from
    - fields (set[str]): A set of field names to remove from the object
    """
    if isinstance(obj, dict):
        for field in fields:
            if field in obj:
                del obj[field]
        for _, value in obj.items():
            remove_fields(value, fields)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for item in obj:
            remove_fields(item, fields)
    elif hasattr(obj, '__dataclass_fields__'):
        raise ValueError(
            'Object must not contain dataclass, consider converting to dict first'
        )
