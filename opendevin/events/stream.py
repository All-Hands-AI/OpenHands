import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Callable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.storage import FileStore, get_file_store

from .event import Event


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


class EventSource(str, Enum):
    AGENT = 'agent'
    USER = 'user'


class EventStream:
    sid: str
    _subscribers: dict[str, Callable] = {}
    _events: list[Event] = []
    _lock = asyncio.Lock()
    _file_store: FileStore

    def __init__(self, sid: str):
        self.sid = sid
        self._file_store = get_file_store()

    def get_filename_for_event(self, event: Event):
        # TODO: change to .id once that prop is in
        return f'{self.sid}/{event._id}.json'  # type: ignore [attr-defined]

    def subscribe(self, id: EventStreamSubscriber, callback: Callable):
        if id in self._subscribers:
            logger.warning('Subscriber subscribed multiple times: ' + id)
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
            to_store = json.dumps(event.to_dict())
            self._file_store.write(self.get_filename_for_event(event), to_store)
            self._events.append(event)
        for key, fn in self._subscribers.items():
            print('calling subscriber', key)
            await fn(event)
