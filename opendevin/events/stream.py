from datetime import datetime
from threading import Lock
from typing import Callable, List

from .event import Event


class EventStream:
    _subscribers: List[Callable] = []
    _events: List[Event] = []
    _lock = Lock()

    def subscribe(self, subscriber: Callable):
        self._subscribers.append(subscriber)

    # TODO: make this not async
    async def add_event(self, event: Event, source: str):
        with self._lock:
            event._id = len(self._events)  # type: ignore [attr-defined]
            event._timestamp = datetime.now()  # type: ignore [attr-defined]
            event._source = source  # type: ignore [attr-defined]
            self._events.append(event)
            for subscriber in self._subscribers:
                await subscriber(event)

    def _notify(self, subscriber: Callable, event: Event):
        subscriber(event)
