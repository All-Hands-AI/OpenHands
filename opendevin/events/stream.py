import asyncio
from datetime import datetime
from enum import Enum
from typing import Callable

from opendevin.core.logger import opendevin_logger as logger

from .event import Event, EventSource


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'


class EventStream:
    def __init__(self):
        self._subscribers: dict[str, Callable] = {}
        self._events: list[Event] = []
        self._lock = asyncio.Lock()

    def subscribe(self, id: EventStreamSubscriber, callback: Callable):
        if id in self._subscribers:
            raise ValueError('Subscriber already exists: ' + id)
        else:
            self._subscribers[id] = callback

    def unsubscribe(self, id: EventStreamSubscriber):
        if id not in self._subscribers:
            logger.warning('Subscriber not found during unsubscribe: ' + id)
        else:
            del self._subscribers[id]

    # TODO: make this not async
    async def add_event(self, event: Event, source: EventSource):
        async with self._lock:
            event._id = len(self._events)  # type: ignore[attr-defined]
            event._timestamp = datetime.now()  # type: ignore[attr-defined]
            event._source = source  # type: ignore[attr-defined]
            self._events.append(event)
        for key, fn in self._subscribers.items():
            await fn(event)
