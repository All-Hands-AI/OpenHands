def remove_fields(obj: dict, fields: set[str]):
    """
    Remove fields from a dictionary.

    Parameters:
    - obj (dict): The dictionary to remove fields from
    - fields (set[str]): A set of field names to remove from the object
    """
    if isinstance(obj, dict):
        for field in fields:
            if field in obj:
                del obj[field]
        for _, value in obj.items():
            remove_fields(value, fields)
    else:
        raise ValueError('Object must be a dictionary')
