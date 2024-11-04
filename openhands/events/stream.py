import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Iterable

from openhands.core.logger import openhands_logger as logger
from openhands.core.utils import json
from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.storage import FileStore
from openhands.utils.async_utils import call_sync_from_async


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SECURITY_ANALYZER = 'security_analyzer'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


async def session_exists(sid: str, file_store: FileStore) -> bool:
    try:
        await call_sync_from_async(file_store.list, f'sessions/{sid}')
        return True
    except FileNotFoundError:
        return False


class AsyncEventStreamWrapper:
    def __init__(self, event_stream, *args, **kwargs):
        self.event_stream = event_stream
        self.args = args
        self.kwargs = kwargs

    async def __aiter__(self):
        loop = asyncio.get_running_loop()

        # Create an async generator that yields events
        for event in self.event_stream.get_events(*self.args, **self.kwargs):
            # Run the blocking get_events() in a thread pool
            yield await loop.run_in_executor(None, lambda e=event: e)  # type: ignore


@dataclass
class EventStream:
    sid: str
    file_store: FileStore
    # For each subscriber ID, there is a stack of callback functions - useful
    # when there are agent delegates
    _subscribers: dict[str, list[Callable]] = field(default_factory=dict)
    _cur_id: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        try:
            content = self.file_store.read(f'sessions/{self.sid}/events.json')
            events = json.loads(content)
            if events:
                # Find highest ID from existing events
                self._cur_id = max(event['id'] for event in events) + 1
            else:
                self._cur_id = 0
        except FileNotFoundError:
            logger.debug(f'No events found for session {self.sid}')
            self._cur_id = 0
            # Initialize empty events file
            self.file_store.write(f'sessions/{self.sid}/events.json', '[]')

    def _get_events_file(self) -> str:
        return f'sessions/{self.sid}/events.json'

    def _read_events(self) -> list[dict]:
        try:
            content = self.file_store.read(self._get_events_file())
            return json.loads(content)
        except FileNotFoundError:
            return []

    def _write_events(self, events: list[dict]) -> None:
        self.file_store.write(self._get_events_file(), json.dumps(events))

    def get_events(
        self,
        start_id=0,
        end_id=None,
        reverse=False,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden=False,
    ) -> Iterable[Event]:
        def should_filter(event: Event):
            if filter_hidden and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter_out_type is not None and isinstance(event, filter_out_type):
                return True
            return False

        with self._lock:
            events = self._read_events()
            if not events:
                return

            if end_id is None:
                end_id = self._cur_id - 1

            # Convert events to Event objects
            event_objects = [event_from_dict(event) for event in events]
            # Filter by ID range
            filtered_events = [e for e in event_objects if start_id <= e.id <= end_id]
            # Apply additional filters
            filtered_events = [e for e in filtered_events if not should_filter(e)]

            if reverse:
                filtered_events.reverse()

            yield from filtered_events

    def get_event(self, id: int) -> Event:
        with self._lock:
            events = self._read_events()
            for event_data in events:
                if event_data['id'] == id:
                    return event_from_dict(event_data)
            raise FileNotFoundError(f'Event with id {id} not found')

    def get_latest_event(self) -> Event:
        return self.get_event(self._cur_id - 1)

    def get_latest_event_id(self) -> int:
        return self._cur_id - 1

    def subscribe(self, id: EventStreamSubscriber, callback: Callable, append=False):
        if id in self._subscribers:
            if append:
                self._subscribers[id].append(callback)
            else:
                raise ValueError('Subscriber already exists: ' + id)
        else:
            self._subscribers[id] = [callback]

    def unsubscribe(self, id: EventStreamSubscriber):
        if id not in self._subscribers:
            logger.warning('Subscriber not found during unsubscribe: ' + id)
        else:
            self._subscribers[id].pop()
            if len(self._subscribers[id]) == 0:
                del self._subscribers[id]

    def add_event(self, event: Event, source: EventSource):
        try:
            asyncio.get_running_loop().create_task(self.async_add_event(event, source))
        except RuntimeError:
            # No event loop running...
            asyncio.run(self.async_add_event(event, source))

    async def async_add_event(self, event: Event, source: EventSource):
        with self._lock:
            event._id = self._cur_id  # type: ignore [attr-defined]
            self._cur_id += 1
            logger.debug(
                f'Adding {type(event).__name__} id={event.id} from {source.name}'
            )
            event._timestamp = datetime.now().isoformat()
            event._source = source  # type: ignore [attr-defined]
            data = event_to_dict(event)

            # Read current events, append new one, and write back
            events = self._read_events()
            events.append(data)
            self._write_events(events)

        tasks = []
        for key in sorted(self._subscribers.keys()):
            stack = self._subscribers[key]
            callback = stack[-1]
            tasks.append(asyncio.create_task(callback(event)))
        if tasks:
            await asyncio.wait(tasks)

    def _callback(self, callback: Callable, event: Event):
        asyncio.run(callback(event))

    def filtered_events_by_source(self, source: EventSource):
        for event in self.get_events():
            if event.source == source:
                yield event

    def clear(self):
        with self._lock:
            self.file_store.delete(f'sessions/{self.sid}')
            self._cur_id = 0
            # Initialize empty events file
            self.file_store.write(self._get_events_file(), '[]')
            # self._subscribers = {}
