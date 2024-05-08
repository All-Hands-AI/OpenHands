from typing import Any

from pydantic import BaseModel, PrivateAttr


class Event(BaseModel):
    _message: str = PrivateAttr(default=None)
    _source: str = PrivateAttr(default=None)

    def to_memory(self):
        return super().model_dump()

    def to_dict(self) -> dict[str, Any]:
        d = self.to_memory()
        d['message'] = self.message
        return d

    @property
    def message(self) -> str:
        return self._message

    @property
    def source(self) -> str:
        return self._source
