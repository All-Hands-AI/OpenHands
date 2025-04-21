import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from functools import partial
from typing import Any, Callable

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


class EventStream(EventStore):
    secrets: dict[str, str]
    # For each subscriber ID, there is a map of callback functions - useful
    # when there are multiple listeners
    _subscribers: dict[str, dict[str, Callable]]
    _lock: threading.Lock
    _queue: queue.Queue[Event]
    _queue_thread: threading.Thread
    _queue_loop: asyncio.AbstractEventLoop | None
    _thread_pools: dict[str, dict[str, ThreadPoolExecutor]]
    _thread_loops: dict[str, dict[str, asyncio.AbstractEventLoop]]
    _write_page_cache: list[dict]

    def __init__(self, sid: str, file_store: FileStore, user_id: str | None = None):
        super().__init__(sid, file_store, user_id)
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
        self._write_page_cache = []

    def _init_thread_loop(self, subscriber_id: str, callback_id: str) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if subscriber_id not in self._thread_loops:
            self._thread_loops[subscriber_id] = {}
        self._thread_loops[subscriber_id][callback_id] = loop

    def close(self) -> None:
        logger.info('Closing EventStream')
        # Log the current thread that's calling close
        current_thread = threading.current_thread()
        logger.info(
            f'Close called from thread: {current_thread.name} (id: {current_thread.ident})'
        )

        # Get a stack trace to see where close is being called from
        import traceback

        stack_trace = ''.join(traceback.format_stack())
        logger.info(f'Close stack trace:\n{stack_trace}')

        # Log the state of subscribers before close
        logger.info(f'Subscribers before close: {list(self._subscribers.keys())}')
        for sid in self._subscribers:
            logger.info(
                f'Callbacks for {sid} before close: {list(self._subscribers[sid].keys())}'
            )

        self._stop_flag.set()
        logger.info('Stop flag set, joining queue thread')
        if self._queue_thread.is_alive():
            logger.info('Queue thread is alive, joining it')
            self._queue_thread.join()
            logger.info('Queue thread joined')
        else:
            logger.info('Queue thread is not alive')

        logger.info('Cleaning up subscribers')
        subscriber_ids = list(self._subscribers.keys())
        logger.info(f'Subscriber IDs to clean up: {subscriber_ids}')

        for subscriber_id in subscriber_ids:
            if subscriber_id not in self._subscribers:
                logger.warning(
                    f'Subscriber {subscriber_id} no longer exists during close'
                )
                continue
            callback_ids = list(self._subscribers[subscriber_id].keys())
            logger.info(f'Callback IDs to clean up for {subscriber_id}: {callback_ids}')

            for callback_id in callback_ids:
                logger.info(
                    f'Cleaning up subscriber {subscriber_id}, callback {callback_id}'
                )
                self._clean_up_subscriber(subscriber_id, callback_id)

        # Clear queue
        logger.info('Clearing queue')
        queue_size = self._queue.qsize()
        logger.info(f'Queue size before clearing: {queue_size}')
        while not self._queue.empty():
            self._queue.get()
        logger.info('Queue cleared')

    def _clean_up_subscriber(self, subscriber_id: str, callback_id: str) -> None:
        logger.info(f'Cleaning up subscriber {subscriber_id}, callback {callback_id}')
        # Log the current state of subscribers before cleanup
        logger.info(f'Subscribers before cleanup: {list(self._subscribers.keys())}')
        if subscriber_id in self._subscribers:
            logger.info(
                f'Callbacks for {subscriber_id} before cleanup: {list(self._subscribers[subscriber_id].keys())}'
            )

        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during cleanup: {subscriber_id}')
            return
        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during cleanup: {callback_id}')
            return

        # Log thread information
        logger.info(
            f"Thread loops before cleanup: {list(self._thread_loops.keys() if hasattr(self, '_thread_loops') else [])}"
        )
        if subscriber_id in self._thread_loops:
            logger.info(
                f'Thread loops for {subscriber_id} before cleanup: {list(self._thread_loops[subscriber_id].keys())}'
            )

        if (
            subscriber_id in self._thread_loops
            and callback_id in self._thread_loops[subscriber_id]
        ):
            loop = self._thread_loops[subscriber_id][callback_id]
            try:
                logger.info(
                    f'Stopping and closing loop for {subscriber_id}/{callback_id}'
                )
                loop.stop()
                loop.close()
            except Exception as e:
                logger.warning(
                    f'Error closing loop for {subscriber_id}/{callback_id}: {e}'
                )
            logger.info(f'Deleting thread loop for {subscriber_id}/{callback_id}')
            del self._thread_loops[subscriber_id][callback_id]

        # Log thread pool information
        logger.info(f'Thread pools before cleanup: {list(self._thread_pools.keys())}')
        if subscriber_id in self._thread_pools:
            logger.info(
                f'Thread pools for {subscriber_id} before cleanup: {list(self._thread_pools[subscriber_id].keys())}'
            )

        if (
            subscriber_id in self._thread_pools
            and callback_id in self._thread_pools[subscriber_id]
        ):
            pool = self._thread_pools[subscriber_id][callback_id]
            logger.info(f'Shutting down thread pool for {subscriber_id}/{callback_id}')
            pool.shutdown()
            logger.info(f'Deleting thread pool for {subscriber_id}/{callback_id}')
            del self._thread_pools[subscriber_id][callback_id]

        logger.info(f'Deleting subscriber {subscriber_id}, callback {callback_id}')
        del self._subscribers[subscriber_id][callback_id]

        # Log the state after cleanup
        logger.info(f'Subscribers after cleanup: {list(self._subscribers.keys())}')
        if subscriber_id in self._subscribers:
            logger.info(
                f'Callbacks for {subscriber_id} after cleanup: {list(self._subscribers[subscriber_id].keys())}'
            )

    def subscribe(
        self,
        subscriber_id: EventStreamSubscriber,
        callback: Callable[[Event], None],
        callback_id: str,
    ) -> None:
        logger.info(f'Subscribing {subscriber_id}, callback {callback_id}')
        # Log the current thread that's calling subscribe
        current_thread = threading.current_thread()
        logger.info(
            f'Subscribe called from thread: {current_thread.name} (id: {current_thread.ident})'
        )

        # Log the state of subscribers before subscribe
        logger.info(f'Subscribers before subscribe: {list(self._subscribers.keys())}')
        if subscriber_id in self._subscribers:
            logger.info(
                f'Callbacks for {subscriber_id} before subscribe: {list(self._subscribers[subscriber_id].keys())}'
            )

        # Get a stack trace to see where subscribe is being called from
        import traceback

        stack_trace = ''.join(traceback.format_stack())
        logger.info(f'Subscribe stack trace:\n{stack_trace}')

        initializer = partial(self._init_thread_loop, subscriber_id, callback_id)
        pool = ThreadPoolExecutor(max_workers=1, initializer=initializer)
        if subscriber_id not in self._subscribers:
            logger.info(f'Creating new subscriber entry for {subscriber_id}')
            self._subscribers[subscriber_id] = {}
            self._thread_pools[subscriber_id] = {}

        if callback_id in self._subscribers[subscriber_id]:
            logger.error(
                f'Callback ID {callback_id} already exists for subscriber {subscriber_id}'
            )
            raise ValueError(
                f'Callback ID on subscriber {subscriber_id} already exists: {callback_id}'
            )

        logger.info(f'Adding callback {callback_id} to subscriber {subscriber_id}')
        self._subscribers[subscriber_id][callback_id] = callback
        self._thread_pools[subscriber_id][callback_id] = pool

        # Log the state after subscribe
        logger.info(f'Subscribers after subscribe: {list(self._subscribers.keys())}')
        logger.info(
            f'Callbacks for {subscriber_id} after subscribe: {list(self._subscribers[subscriber_id].keys())}'
        )

    def unsubscribe(
        self, subscriber_id: EventStreamSubscriber, callback_id: str
    ) -> None:
        logger.info(f'Unsubscribing {subscriber_id}, callback {callback_id}')
        # Log the current thread that's calling unsubscribe
        current_thread = threading.current_thread()
        logger.info(
            f'Unsubscribe called from thread: {current_thread.name} (id: {current_thread.ident})'
        )

        # Log the state of subscribers before unsubscribe
        logger.info(f'Subscribers before unsubscribe: {list(self._subscribers.keys())}')
        if subscriber_id in self._subscribers:
            logger.info(
                f'Callbacks for {subscriber_id} before unsubscribe: {list(self._subscribers[subscriber_id].keys())}'
            )

        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during unsubscribe: {subscriber_id}')
            return

        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during unsubscribe: {callback_id}')
            return

        # Get a stack trace to see where unsubscribe is being called from
        import traceback

        stack_trace = ''.join(traceback.format_stack())
        logger.info(f'Unsubscribe stack trace:\n{stack_trace}')

        self._clean_up_subscriber(subscriber_id, callback_id)

    def add_event(self, event: Event, source: EventSource) -> None:
        if event.id != Event.INVALID_ID:
            raise ValueError(
                f'Event already has an ID:{event.id}. It was probably added back to the EventStream from inside a handler, triggering a loop.'
            )
        event._timestamp = datetime.now().isoformat()
        event._source = source  # type: ignore [attr-defined]
        with self._lock:
            event._id = self.cur_id  # type: ignore [attr-defined]
            self.cur_id += 1

            # Take a copy of the current write page
            current_write_page = self._write_page_cache

            data = event_to_dict(event)
            data = self._replace_secrets(data)
            event = event_from_dict(data)
            current_write_page.append(data)

            # If the page is full, create a new page for future events / other threads to use
            if len(current_write_page) == self.cache_size:
                self._write_page_cache = []

        if event.id is not None:
            # Write the event to the store - this can take some time
            self.file_store.write(
                self._get_filename_for_id(event.id, self.user_id), json.dumps(data)
            )

            # Store the cache page last - if it is not present during reads then it will simply be bypassed.
            self._store_cache_page(current_write_page)
        self._queue.put(event)

    def _store_cache_page(self, current_write_page: list[dict]):
        """Store a page in the cache. Reading individual events is slow when there are a lot of them, so we use pages."""
        if len(current_write_page) < self.cache_size:
            return
        start = current_write_page[0]['id']
        end = start + self.cache_size
        contents = json.dumps(current_write_page)
        cache_filename = self._get_filename_for_cache(start, end)
        self.file_store.write(cache_filename, contents)

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
            # Get a sorted copy of subscriber keys to avoid modification during iteration
            subscriber_keys = sorted(self._subscribers.keys())
            logger.info(f'Subscriber keys: {subscriber_keys}')

            for key in subscriber_keys:
                logger.info(f'Processing subscriber key: {key}')

                # Check if the subscriber still exists
                if key not in self._subscribers:
                    logger.warning(f'Subscriber {key} no longer exists')
                    continue

                callbacks = self._subscribers[key]
                # Log the state of callbacks dictionary before iteration
                logger.info(
                    f'Callbacks before iteration for {key}: {list(callbacks.keys())}'
                )

                for callback_id in callbacks:
                    logger.info(f'Processing callback_id: {callback_id}')
                    callback = callbacks[callback_id]
                    logger.info(f'Retrieved callback for {callback_id}: {callback}')
                    pool = self._thread_pools[key][callback_id]
                    logger.info(f'Submitting callback {callback_id} to thread pool')
                    future = pool.submit(callback, event)
                    future.add_done_callback(self._make_error_handler(callback_id, key))

                # Log the state of callbacks dictionary after processing this key
                if key in self._subscribers:
                    logger.info(
                        f'Callbacks after processing {key}: {list(self._subscribers[key].keys())}'
                    )
                else:
                    logger.info(f'Subscriber {key} was removed during processing')

    def _make_error_handler(
        self, callback_id: str, subscriber_id: str
    ) -> Callable[[Any], None]:
        def _handle_callback_error(fut: Any) -> None:
            logger.info(
                f'Handling callback result for {callback_id} in subscriber {subscriber_id}'
            )
            # Log the current thread that's handling the callback result
            current_thread = threading.current_thread()
            logger.info(
                f'Callback handler running in thread: {current_thread.name} (id: {current_thread.ident})'
            )

            try:
                # This will raise any exception that occurred during callback execution
                logger.info(f'Callback {callback_id} completed successfully')

                # Log the current state of subscribers and thread pools after successful execution
                logger.info(
                    f'After successful callback - Current subscribers: {list(self._subscribers.keys())}'
                )
                if subscriber_id in self._subscribers:
                    logger.info(
                        f'After successful callback - Current callbacks for {subscriber_id}: {list(self._subscribers[subscriber_id].keys())}'
                    )
            except Exception as e:
                logger.error(
                    f'Error in event callback {callback_id} for subscriber {subscriber_id}: {str(e)}',
                )
                # Log the current state of subscribers and thread pools
                logger.info(
                    f'After error in callback - Current subscribers: {list(self._subscribers.keys())}'
                )
                if subscriber_id in self._subscribers:
                    logger.info(
                        f'After error in callback - Current callbacks for {subscriber_id}: {list(self._subscribers[subscriber_id].keys())}'
                    )
                logger.info(
                    f'After error in callback - Current thread pools: {list(self._thread_pools.keys())}'
                )
                if subscriber_id in self._thread_pools:
                    logger.info(
                        f'After error in callback - Current thread pools for {subscriber_id}: {list(self._thread_pools[subscriber_id].keys())}'
                    )

                # Get a stack trace to see where the error occurred
                import traceback

                stack_trace = ''.join(traceback.format_stack())
                logger.info(f'Error stack trace:\n{stack_trace}')

                # Re-raise in the main thread so the error is not swallowed
                raise e

        return _handle_callback_error
