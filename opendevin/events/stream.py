import asyncio
from datetime import datetime
from threading import Lock
from typing import Callable, Dict, List

from .event import Event


class EventStream:
    _subscribers: Dict[str, Callable] = {}
    _events: List[Event] = []
    _lock = Lock()

    def subscribe(self, id: str, subscriber: Callable):
        if id in self._subscribers:
            raise ValueError('Subscriber already exists: ' + id)
        self._subscribers[id] = subscriber

    def unsubscribe(self, id: str):
        if id not in self._subscribers:
            raise ValueError('Subscriber does not exist: ' + id)
        del self._subscribers[id]

    # TODO: make this not async
    async def add_event(self, event: Event, source: str):
        with self._lock:
            event._id = len(self._events)  # type: ignore [attr-defined]
            event._timestamp = datetime.now()  # type: ignore [attr-defined]
            event._source = source  # type: ignore [attr-defined]
            self._events.append(event)
            for key, fn in self._subscribers.items():
                asyncio.create_task(fn(event))
