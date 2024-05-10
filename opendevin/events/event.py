from dataclasses import dataclass


@dataclass
class Event:
    @property
    def message(self) -> str:
        return self._message  # type: ignore [attr-defined]

    @property
    def source(self) -> str:
        return self._source  # type: ignore [attr-defined]
