import json
from dataclasses import asdict, dataclass
from datetime import datetime


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


# TODO: move `content` into `extras`
TOP_KEYS = ['id', 'timestamp', 'source', 'message', 'action', 'observation', 'content']


@dataclass
class Event:
    def to_dict(self):
        props = asdict(self)
        d = {}
        for key in TOP_KEYS:
            if hasattr(self, key):
                d[key] = getattr(self, key)
            elif hasattr(self, f'_{key}'):
                d[key] = getattr(self, f'_{key}')
            props.pop(key, None)
        if 'action' in d:
            d['args'] = props
        elif 'observation' in d:
            d['extras'] = props
        else:
            raise ValueError('Event must be either action or observation')
        return d

    def to_memory(self):
        d = self.to_dict()
        d.pop('id', None)
        d.pop('timestamp', None)
        d.pop('message', None)

    def to_json(self):
        return json.dumps(self.to_dict(), default=json_serial)

    @property
    def message(self) -> str:
        return self._message  # type: ignore [attr-defined]

    @property
    def source(self) -> str:
        return self._source  # type: ignore [attr-defined]
