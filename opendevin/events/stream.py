import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Callable, Iterable

from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.serialization.event import event_from_dict, event_to_dict
from opendevin.storage import FileStore, get_file_store

from .event import Event
from .serialization.event import EventSource


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


class EventStream:
    sid: str
    _subscribers: dict[str, Callable]
    _cur_id: int
    _lock: asyncio.Lock
    _file_store: FileStore

    def __init__(self, sid: str):
        self.sid = sid
        self._file_store = get_file_store()
        self._subscribers = {}
        self._cur_id = 0
        self._lock = asyncio.Lock()
        self._reinitialize_from_file_store()

    def _reinitialize_from_file_store(self):
        events = self._file_store.list(f'sessions/{self.sid}/events')
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if id >= self._cur_id:
                self._cur_id = id + 1

    def _get_filename_for_id(self, id: int) -> str:
        return f'sessions/{self.sid}/events/{id}.json'

    def _get_id_from_filename(self, filename: str) -> int:
        return int(filename.split('/')[-1].split('.')[0])

    def get_events(self, start_id=0, end_id=None) -> Iterable[Event]:
        events = self._file_store.list(f'sessions/{self.sid}/events')
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if start_id <= id and (end_id is None or id <= end_id):
                event = self.get_event(id)
                yield event

    def get_event(self, id: int) -> Event:
        filename = self._get_filename_for_id(id)
        content = self._file_store.read(filename)
        data = json.loads(content)
        return event_from_dict(data)

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
            event._id = self._cur_id  # type: ignore [attr-defined]
            self._cur_id += 1
        event._timestamp = datetime.now()  # type: ignore [attr-defined]
        event._source = source  # type: ignore [attr-defined]
        data = event_to_dict(event)
        self._file_store.write(self._get_filename_for_id(event.id), json.dumps(data))
        for key, fn in self._subscribers.items():
            await fn(event)
