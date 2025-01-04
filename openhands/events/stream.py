import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from queue import Queue
from typing import Callable, Iterable

from openhands.core.logger import openhands_logger as logger
from openhands.core.utils import json
from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.storage import FileStore
from openhands.storage.locations import (
    get_conversation_dir,
    get_conversation_event_filename,
    get_conversation_events_dir,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.shutdown_listener import should_continue


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SECURITY_ANALYZER = 'security_analyzer'
    RESOLVER = 'openhands_resolver'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MAIN = 'main'
    TEST = 'test'


async def session_exists(sid: str, file_store: FileStore) -> bool:
    try:
        await call_sync_from_async(file_store.list, get_conversation_dir(sid))
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


class EventStream:
    sid: str
    file_store: FileStore
    # For each subscriber ID, there is a map of callback functions - useful
    # when there are multiple listeners
    _subscribers: dict[str, dict[str, Callable]]
    _cur_id: int = 0
    _lock: threading.Lock

    def __init__(self, sid: str, file_store: FileStore, num_workers: int = 1):
        self.sid = sid
        self.file_store = file_store
        self._queue: Queue[Event] = Queue()
        self._thread_pools: dict[str, dict[str, ThreadPoolExecutor]] = {}
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True
        self._queue_thread.start()
        self._subscribers = {}
        self._lock = threading.Lock()
        self._cur_id = 0

        # load the stream
        self.__post_init__()

    def __post_init__(self) -> None:
        try:
            events = self.file_store.list(get_conversation_events_dir(self.sid))
        except FileNotFoundError:
            logger.debug(f'No events found for session {self.sid}')
            self._cur_id = 0
            return

        # if we have events, we need to find the highest id to prepare for new events
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if id >= self._cur_id:
                self._cur_id = id + 1

    def _init_thread_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    def _get_filename_for_id(self, id: int) -> str:
        return get_conversation_event_filename(self.sid, id)

    @staticmethod
    def _get_id_from_filename(filename: str) -> int:
        try:
            return int(filename.split('/')[-1].split('.')[0])
        except ValueError:
            logger.warning(f'get id from filename ({filename}) failed.')
            return -1

    def get_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden=False,
    ) -> Iterable[Event]:
        """
        Retrieve events from the event stream, optionally filtering out events of a given type
        and events marked as hidden.

        Args:
            start_id: The ID of the first event to retrieve. Defaults to 0.
            end_id: The ID of the last event to retrieve. Defaults to the last event in the stream.
            reverse: Whether to retrieve events in reverse order. Defaults to False.
            filter_out_type: A tuple of event types to filter out. Typically used to filter out backend events from the agent.
            filter_hidden: If True, filters out events with the 'hidden' attribute set to True.

        Yields:
            Events from the stream that match the criteria.
        """

        def should_filter(event: Event):
            if filter_hidden and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter_out_type is not None and isinstance(event, filter_out_type):
                return True
            return False

        if reverse:
            if end_id is None:
                end_id = self._cur_id - 1
            event_id = end_id
            while event_id >= start_id:
                try:
                    event = self.get_event(event_id)
                    if not should_filter(event):
                        yield event
                except FileNotFoundError:
                    logger.debug(f'No event found for ID {event_id}')
                event_id -= 1
        else:
            event_id = start_id
            while should_continue():
                if end_id is not None and event_id > end_id:
                    break
                try:
                    event = self.get_event(event_id)
                    if not should_filter(event):
                        yield event
                except FileNotFoundError:
                    break
                event_id += 1

    def get_event(self, id: int) -> Event:
        filename = self._get_filename_for_id(id)
        content = self.file_store.read(filename)
        data = json.loads(content)
        return event_from_dict(data)

    def get_latest_event(self) -> Event:
        return self.get_event(self._cur_id - 1)

    def get_latest_event_id(self) -> int:
        return self._cur_id - 1

    def subscribe(
        self, subscriber_id: EventStreamSubscriber, callback: Callable, callback_id: str
    ):
        pool = ThreadPoolExecutor(max_workers=1, initializer=self._init_thread_loop)
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
            self._thread_pools[subscriber_id] = {}

        if callback_id in self._subscribers[subscriber_id]:
            raise ValueError(
                f'Callback ID on subscriber {subscriber_id} already exists: {callback_id}'
            )

        self._subscribers[subscriber_id][callback_id] = callback
        self._thread_pools[subscriber_id][callback_id] = pool

    def unsubscribe(self, subscriber_id: EventStreamSubscriber, callback_id: str):
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during unsubscribe: {subscriber_id}')
            return

        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during unsubscribe: {callback_id}')
            return

        del self._subscribers[subscriber_id][callback_id]

    def add_event(self, event: Event, source: EventSource):
        if hasattr(event, '_id') and event.id is not None:
            raise ValueError(
                'Event already has an ID. It was probably added back to the EventStream from inside a handler, trigging a loop.'
            )
        with self._lock:
            event._id = self._cur_id  # type: ignore [attr-defined]
            self._cur_id += 1
        logger.debug(f'Adding {type(event).__name__} id={event.id} from {source.name}')
        event._timestamp = datetime.now().isoformat()
        event._source = source  # type: ignore [attr-defined]
        data = event_to_dict(event)
        if event.id is not None:
            self.file_store.write(self._get_filename_for_id(event.id), json.dumps(data))
        self._queue.put(event)

    def _run_queue_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._process_queue())

    async def _process_queue(self):
        while should_continue():
            event = self._queue.get()
            for key in sorted(self._subscribers.keys()):
                callbacks = self._subscribers[key]
                for callback_id in callbacks:
                    callback = callbacks[callback_id]
                    pool = self._thread_pools[key][callback_id]
                    future = pool.submit(callback, event)
                    future.add_done_callback(self._make_error_handler(callback_id, key))

    def _make_error_handler(self, callback_id: str, subscriber_id: str):
        def _handle_callback_error(fut):
            try:
                # This will raise any exception that occurred during callback execution
                fut.result()
            except Exception as e:
                logger.error(
                    f'Error in event callback {callback_id} for subscriber {subscriber_id}: {str(e)}',
                    exc_info=True,
                    stack_info=True,
                )
                # Re-raise in the main thread so the error is not swallowed
                raise e

        return _handle_callback_error

    def filtered_events_by_source(self, source: EventSource):
        for event in self.get_events():
            if event.source == source:
                yield event

    def _should_filter_event(
        self,
        event,
        query: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bool:
        """Check if an event should be filtered out based on the given criteria.

        Args:
            event: The event to check
            query (str, optional): Text to search for in event content
            event_type (str, optional): Filter by event type (e.g., "FileReadAction")
            source (str, optional): Filter by event source
            start_date (str, optional): Filter events after this date (ISO format)
            end_date (str, optional): Filter events before this date (ISO format)

        Returns:
            bool: True if the event should be filtered out, False if it matches all criteria
        """
        if event_type and not event.__class__.__name__ == event_type:
            return True

        if source and not event.source.value == source:
            return True

        if start_date and event.timestamp < start_date:
            return True

        if end_date and event.timestamp > end_date:
            return True

        # Text search in event content if query provided
        if query:
            event_dict = event_to_dict(event)
            event_str = str(event_dict).lower()
            if query.lower() not in event_str:
                return True

        return False

    def get_matching_events(
        self,
        query: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        start_id: int = 0,
        limit: int = 100,
    ) -> list:
        """Get matching events from the event stream based on filters.

        Args:
            query (str, optional): Text to search for in event content
            event_type (str, optional): Filter by event type (e.g., "FileReadAction")
            source (str, optional): Filter by event source
            start_date (str, optional): Filter events after this date (ISO format)
            end_date (str, optional): Filter events before this date (ISO format)
            start_id (int): Starting ID in the event stream. Defaults to 0
            limit (int): Maximum number of events to return. Must be between 1 and 100. Defaults to 100

        Returns:
            list: List of matching events (as dicts)

        Raises:
            ValueError: If limit is less than 1 or greater than 100
        """
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')

        matching_events: list = []

        for event in self.get_events(start_id=start_id):
            if self._should_filter_event(
                event, query, event_type, source, start_date, end_date
            ):
                continue

            matching_events.append(event_to_dict(event))

            # Stop if we have enough events
            if len(matching_events) >= limit:
                break

        return matching_events
