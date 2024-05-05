from dataclasses import asdict, dataclass


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
        return self._message  # type: ignore [attr-defined]

    @property
    def source(self) -> str:
        return self._source  # type: ignore [attr-defined]
