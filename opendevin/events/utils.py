def _remove_fields(obj, fields: set[str]):
    """
    Remove fields from an object

    Parameters:
    - obj (Object): The object to remove fields from
    - fields (set[str]): A set of field names to remove from the object
    """
    if isinstance(obj, dict):
        for field in fields:
            if field in obj:
                del obj[field]
        for _, value in obj.items():
            _remove_fields(value, fields)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for item in obj:
            _remove_fields(item, fields)
    elif hasattr(obj, '__dataclass_fields__'):
        for field in fields:
            if field in obj.__dataclass_fields__:
                setattr(obj, field, None)
        for value in obj.__dict__.values():
            _remove_fields(value, fields)
