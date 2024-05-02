import asyncio
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

    def add_event(self, event: Event):
        with self._lock:
            event.id = len(self._events)  # type: ignore [attr-defined]
            event.timestamp = datetime.now()  # type: ignore [attr-defined]
            self._events.append(event)
            for subscriber in self._subscribers:
                asyncio.create_task(self._notify(subscriber, event))

    def _notify(self, subscriber: Callable, event: Event):
        subscriber(event)


singleton = EventStream()


def get_event_stream():
    return singleton
