from abc import ABC, abstractmethod
from typing import Union


class StreamMixin:
    def __init__(self, generator):
        self.generator = generator
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.closed:
            raise StopIteration
        else:
            return next(self.generator)


class CancellableStream(StreamMixin, ABC):
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def exit_code(self) -> Union[int, None]:
        pass
