import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Callable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.serialization.event import event_from_dict, event_to_dict
from opendevin.storage import FileStore, get_file_store

from .event import Event, EventSource


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


class EventStream:
    sid: str
    _subscribers: dict[str, Callable]
    _events: list[Event]
    _lock: asyncio.Lock
    _file_store: FileStore

    def __init__(self, sid: str):
        self.sid = sid
        self._file_store = get_file_store()
        self._subscribers = {}
        self._events = []
        self._lock = asyncio.Lock()

    def _get_filename_for_event(self, event: Event):
        # TODO: change to .id once that prop is in
        return f'sessions/{self.sid}/events/{event._id}.json'  # type: ignore [attr-defined]

    async def _rehydrate(self):
        async with self._lock:
            self._events = []
            events = self._file_store.list(f'sessions/{self.sid}/events')
            for event_str in events:
                content = self._file_store.read(event_str)
                data = json.loads(content)
                event = event_from_dict(data)
                self._events.append(event)

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
            event._id = len(self._events)  # type: ignore [attr-defined]
            event._timestamp = datetime.now()  # type: ignore [attr-defined]
            event._source = source  # type: ignore [attr-defined]
            self._file_store.write(
                self._get_filename_for_event(event), json.dumps(event_to_dict(event))
            )
            self._events.append(event)
        for key, fn in self._subscribers.items():
            await fn(event)
