from abc import abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')


class ItemStore(Generic[T]):
    @abstractmethod
    def load(self, id: str) -> T | None:
        """Load an item"""

    @abstractmethod
    def store(self, id: str, item: T):
        """Store an item"""
