from openhands.events.event import Event
from openhands.events.serialization.event import event_from_dict


def remove_fields(obj, fields: set[str]):
    """Remove fields from an object.

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
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            remove_fields(item, fields)
    elif hasattr(obj, '__dataclass_fields__'):
        raise ValueError(
            'Object must not contain dataclass, consider converting to dict first'
        )


def str_to_event_type(event: str | None) -> Event | None:
    if not event:
        return None

    for event_type in ['observation', 'action']:
        try:
            return event_from_dict({event_type: event})
        except Exception:
            continue

    return None
