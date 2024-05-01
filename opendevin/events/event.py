from dataclasses import dataclass


@dataclass
class Event:
    def to_memory(self):
        return self.__dict__

    def to_dict(self):
        d = self.to_memory()
        d['message'] = self.message
        return d

    @property
    def message(self) -> str:
        return self.message
