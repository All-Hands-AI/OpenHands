import datetime
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional


class EventSource(str, Enum):
    AGENT = 'agent'
    USER = 'user'


@dataclass
class Event:
    def to_memory(self):
        return asdict(self)

    def to_dict(self):
        d = self.to_memory()
        d['message'] = self.message
        return d

    @property
    def message(self) -> str:
        if hasattr(self, '_message'):
            return self._message  # type: ignore [attr-defined]
        return ''

    @property
    def id(self) -> int:
        if hasattr(self, '_id'):
            return self._id  # type: ignore [attr-defined]
        return -1

    @property
    def timestamp(self) -> Optional[datetime.datetime]:
        if hasattr(self, '_timestamp'):
            return self._timestamp  # type: ignore [attr-defined]
        return None

    @property
    def source(self) -> Optional[EventSource]:
        if hasattr(self, '_source'):
            return self._source  # type: ignore [attr-defined]
        return None

    @property
    def cause(self) -> Optional[int]:
        if hasattr(self, '_cause'):
            return self._cause  # type: ignore [attr-defined]
        return None
