import json
from dataclasses import dataclass
from datetime import datetime

from opendevin.events.serialization.event import event_to_dict


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


@dataclass
class Event:
    def to_dict(self):
        return event_to_dict(self)

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
