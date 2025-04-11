import asyncio
import queue
import threading
import collections
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from functools import partial
from typing import Any, Callable
import os

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.events.event_store import EventStore
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.io import json
from openhands.storage import FileStore
from openhands.storage.locations import (
    get_conversation_dir,
)
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.shutdown_listener import should_continue
from openhands.storage.local import LocalFileStore # Assuming LocalFileStore


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    SECURITY_ANALYZER = 'security_analyzer'
    RESOLVER = 'openhands_resolver'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MEMORY = 'memory'
    MAIN = 'main'
    TEST = 'test'


async def session_exists(
    sid: str, file_store: FileStore, user_id: str | None = None
) -> bool:
    try:
        await call_sync_from_async(file_store.list, get_conversation_dir(sid, user_id))
        return True
    except FileNotFoundError:
        return False


# Define a constant for the cache size
RECENT_EVENTS_CACHE_SIZE = 50


class EventStream(EventStore):
    secrets: dict[str, str]
    _subscribers: dict[str, dict[str, Callable]]
    _lock: threading.Lock
    _queue: queue.Queue[Event]
    _queue_thread: threading.Thread
    _queue_loop: asyncio.AbstractEventLoop | None
    _thread_pools: dict[str, dict[str, ThreadPoolExecutor]]
    _thread_loops: dict[str, dict[str, asyncio.AbstractEventLoop]]
    _recent_events_cache: collections.deque[Event]

    def __init__(self, sid: str, file_store: FileStore, user_id: str | None = None, cur_id: int = -1):
        super().__init__(sid, file_store, user_id, cur_id=cur_id)
        self._stop_flag = threading.Event()
        self._queue: queue.Queue[Event] = queue.Queue()
        self._thread_pools = {}
        self._thread_loops = {}
        self._queue_loop = None
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True
        self._queue_thread.start()
        self._subscribers = {}
        self._lock = threading.Lock()
        self.secrets = {}
        # Initialize the recent events cache
        self._recent_events_cache = collections.deque(maxlen=RECENT_EVENTS_CACHE_SIZE)
        # TODO: Consider pre-populating the cache here by reading last N from file?
        # For now, it will populate as new events are added.

    def _init_thread_loop(self, subscriber_id: str, callback_id: str) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if subscriber_id not in self._thread_loops:
            self._thread_loops[subscriber_id] = {}
        self._thread_loops[subscriber_id][callback_id] = loop

    def close(self) -> None:
        self._stop_flag.set()
        if self._queue_thread.is_alive():
            self._queue_thread.join()

        subscriber_ids = list(self._subscribers.keys())
        for subscriber_id in subscriber_ids:
            callback_ids = list(self._subscribers[subscriber_id].keys())
            for callback_id in callback_ids:
                self._clean_up_subscriber(subscriber_id, callback_id)

        # Clear queue
        while not self._queue.empty():
            self._queue.get()

    def _clean_up_subscriber(self, subscriber_id: str, callback_id: str) -> None:
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during cleanup: {subscriber_id}')
            return
        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during cleanup: {callback_id}')
            return
        if (
            subscriber_id in self._thread_loops
            and callback_id in self._thread_loops[subscriber_id]
        ):
            loop = self._thread_loops[subscriber_id][callback_id]
            try:
                loop.stop()
                loop.close()
            except Exception as e:
                logger.warning(
                    f'Error closing loop for {subscriber_id}/{callback_id}: {e}'
                )
            del self._thread_loops[subscriber_id][callback_id]

        if (
            subscriber_id in self._thread_pools
            and callback_id in self._thread_pools[subscriber_id]
        ):
            pool = self._thread_pools[subscriber_id][callback_id]
            pool.shutdown()
            del self._thread_pools[subscriber_id][callback_id]

        del self._subscribers[subscriber_id][callback_id]

    def subscribe(
        self,
        subscriber_id: EventStreamSubscriber,
        callback: Callable[[Event], None],
        callback_id: str,
    ) -> None:
        initializer = partial(self._init_thread_loop, subscriber_id, callback_id)
        pool = ThreadPoolExecutor(max_workers=1, initializer=initializer)
        if subscriber_id not in self._subscribers:
            self._subscribers[subscriber_id] = {}
            self._thread_pools[subscriber_id] = {}

        if callback_id in self._subscribers[subscriber_id]:
            raise ValueError(
                f'Callback ID on subscriber {subscriber_id} already exists: {callback_id}'
            )

        self._subscribers[subscriber_id][callback_id] = callback
        self._thread_pools[subscriber_id][callback_id] = pool

    def unsubscribe(
        self, subscriber_id: EventStreamSubscriber, callback_id: str
    ) -> None:
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during unsubscribe: {subscriber_id}')
            return

        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during unsubscribe: {callback_id}')
            return

        self._clean_up_subscriber(subscriber_id, callback_id)

    def _get_events_log_filename(self) -> str:
        """Gets the relative path for the events log file."""
        return f'{get_conversation_dir(self.sid, self.user_id)}events.jsonl'

    def _sync_append_event_to_file(self, event_id: int, data_to_write: dict) -> None:
        """Synchronous helper to append event data to the log file."""
        log_filename_relative = self._get_events_log_filename()
        try:
            if isinstance(self.file_store, LocalFileStore):
                log_filename_abs = self.file_store.get_full_path(log_filename_relative)
                os.makedirs(os.path.dirname(log_filename_abs), exist_ok=True)
                with open(log_filename_abs, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(data_to_write) + '\n')
            else:
                # Fallback read-modify-write (already synchronous)
                logger.warning("FileStore is not LocalFileStore, using synchronous read-modify-write for event log append.")
                try:
                    existing_content = self.file_store.read(log_filename_relative)
                except FileNotFoundError:
                    existing_content = ""
                if existing_content and not existing_content.endswith('\n'):
                    existing_content += '\n'
                new_line = json.dumps(data_to_write) + '\n'
                full_content = existing_content + new_line
                self.file_store.write(log_filename_relative, full_content)
        except Exception as e:
            # Log error but don't crash the background task if possible
            logger.error(f'Failed to write event {event_id} to {log_filename_relative} in background: {e}')
            # Re-raise if necessary, or handle more gracefully depending on desired behavior
            # raise e

    async def add_event(self, event: Event, source: EventSource) -> None:
        """Adds an event, performing file write asynchronously."""
        # Assign ID and metadata synchronously and quickly
        with self._lock:
            event._id = self.cur_id
            self.cur_id += 1
            event_id = event.id # Get ID for logging/writing
        logger.debug(f'Assigning event ID {event_id} ({type(event).__name__}) from {source.name}')
        event._timestamp = datetime.now().isoformat()
        event._source = source
        data = event_to_dict(event)
        data = self._replace_secrets(data)

        event_object_for_cache_and_queue = event_from_dict(data)

        # Add to in-memory cache immediately (synchronous, fast)
        with self._lock:
            self._recent_events_cache.append(event_object_for_cache_and_queue)

        # Put event onto internal queue for subscribers (synchronous, fast)
        self._queue.put(event_object_for_cache_and_queue)

        # Schedule the file write to run in the background without blocking
        if event_id is not None:
            loop = asyncio.get_running_loop()
            # Use partial to pass arguments to the sync helper
            write_task = partial(self._sync_append_event_to_file, event_id, data)
            # Schedule the task - no need to await the result here
            loop.run_in_executor(None, write_task)
            logger.debug(f'Scheduled background write for event ID {event_id}')
        else:
            logger.warning('Event ID was None, skipping file write.')

    def set_secrets(self, secrets: dict[str, str]) -> None:
        self.secrets = secrets.copy()

    def update_secrets(self, secrets: dict[str, str]) -> None:
        self.secrets.update(secrets)

    def _replace_secrets(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in data:
            if isinstance(data[key], dict):
                data[key] = self._replace_secrets(data[key])
            elif isinstance(data[key], str):
                for secret in self.secrets.values():
                    data[key] = data[key].replace(secret, '<secret_hidden>')
        return data

    def _run_queue_loop(self) -> None:
        self._queue_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._queue_loop)
        try:
            self._queue_loop.run_until_complete(self._process_queue())
        finally:
            self._queue_loop.close()

    async def _process_queue(self) -> None:
        while should_continue() and not self._stop_flag.is_set():
            event = None
            try:
                event = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # pass each event to each callback in order
            for key in sorted(self._subscribers.keys()):
                callbacks = self._subscribers[key]
                for callback_id in callbacks:
                    callback = callbacks[callback_id]
                    pool = self._thread_pools[key][callback_id]
                    future = pool.submit(callback, event)
                    future.add_done_callback(self._make_error_handler(callback_id, key))

    def _make_error_handler(
        self, callback_id: str, subscriber_id: str
    ) -> Callable[[Any], None]:
        def _handle_callback_error(fut: Any) -> None:
            try:
                # This will raise any exception that occurred during callback execution
                fut.result()
            except Exception as e:
                logger.error(
                    f'Error in event callback {callback_id} for subscriber {subscriber_id}: {str(e)}',
                )
                # Re-raise in the main thread so the error is not swallowed
                raise e

        return _handle_callback_error

    def get_recent_events_from_cache(
        self,
        max_events: int = RECENT_EVENTS_CACHE_SIZE,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden: bool = False
    ) -> list[Event]:
        """Efficiently retrieve the most recent events from the in-memory cache."""

        def should_filter(event: Event) -> bool:
            if filter_hidden and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter_out_type is not None and isinstance(event, filter_out_type):
                return True
            return False

        # Get events directly from the deque (which stores them in insertion order)
        # Note: deque doesn't support slicing like list, iterate instead.
        cached_events: list[Event] = []
        with self._lock: # Protect cache access
            # Iterate in reverse to easily limit to max_events from the end
            for event in reversed(self._recent_events_cache):
                if not should_filter(event):
                     cached_events.append(event)
                     if len(cached_events) >= max_events:
                         break
        # Reverse again to return in chronological order
        return cached_events[::-1]
