import json
from dataclasses import dataclass
from typing import Iterable

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.events.event_filter import EventFilter
from openhands.events.event_store_abc import EventStoreABC
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.shared import config as shared_config
from openhands.storage.database import db_file_store
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    get_conversation_dir,
    get_conversation_event_filename,
    get_conversation_events_dir,
)
from openhands.utils.shutdown_listener import should_continue


@dataclass(frozen=True)
class _CachePage:
    events: list[dict] | None
    start: int
    end: int

    def covers(self, global_index: int) -> bool:
        if global_index < self.start:
            return False
        if global_index >= self.end:
            return False
        return True

    def get_event(self, global_index: int) -> Event | None:
        # If there was not actually a cached page, return None
        if not self.events:
            return None
        local_index = global_index - self.start
        return event_from_dict(self.events[local_index])


_DUMMY_PAGE = _CachePage(None, 1, -1)


@dataclass
class EventStore(EventStoreABC):
    """
    A stored list of events backing a conversation
    """

    sid: str
    file_store: FileStore
    user_id: str | None
    cur_id: int = -1  # We fix this in post init if it is not specified
    cache_size: int = 25

    def __post_init__(self) -> None:
        if self.cur_id >= 0:
            return
        if shared_config.file_store == 'database':
            self.cur_id = db_file_store._get_latest_event_id(self.sid)
        else:
            events = []
            try:
                events_dir = get_conversation_events_dir(self.sid, self.user_id)
                events = self.file_store.list(events_dir)
            except FileNotFoundError:
                logger.debug(f'No events found for session {self.sid} at {events_dir}')
                events = []

            # if self.user_id:
            #     # During transition to new location, try old location if user_id is set
            #     # TODO: remove this code after 5/1/2025
            #     try:
            #         events_dir = get_conversation_events_dir(self.sid)
            #         events += self.file_store.list(events_dir)
            #     except FileNotFoundError:
            #         logger.debug(f'No events found for session {self.sid} at {events_dir}')

            if not events:
                self.cur_id = 0
                return
            # if we have events, we need to find the highest id to prepare for new events
            for event_str in events:
                id = self._get_id_from_filename(event_str)
                if id >= self.cur_id:
                    self.cur_id = id + 1

    def search_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter: EventFilter | None = None,
        limit: int | None = None,
    ) -> Iterable[Event]:
        """
        Retrieve events from the event stream, optionally filtering out events of a given type
        and events marked as hidden.

        Args:
            start_id: The ID of the first event to retrieve. Defaults to 0.
            end_id: The ID of the last event to retrieve. Defaults to the last event in the stream.
            reverse: Whether to retrieve events in reverse order. Defaults to False.
            filter: EventFilter to use

        Yields:
            Events from the stream that match the criteria.
        """

        def should_filter(event: Event) -> bool:
            if filter and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter is not None and filter.exclude(event):
                return True
            return False

        if end_id is None:
            end_id = self.cur_id
        else:
            end_id += 1  # From inclusive to exclusive

        num_results = 0
        if shared_config.file_store == 'database':
            events = db_file_store._get_events_from_start_id(self.sid, start_id)
            for event_dict in events:
                parsed_event = event_from_dict(event_dict)
                if parsed_event and not should_filter(parsed_event):
                    yield parsed_event
                    num_results += 1
                    if limit and limit <= num_results:
                        return
        else:
            cache_page = _DUMMY_PAGE

            if reverse:
                step = -1
                start_id, end_id = end_id, start_id
                start_id -= 1
                end_id -= 1
            else:
                step = 1

            for index in range(start_id, end_id, step):
                if not should_continue():
                    return
                if not cache_page.covers(index):
                    cache_page = self._load_cache_page_for_index(index)
                event = cache_page.get_event(index)
                if event is None:
                    try:
                        event = self.get_event(index)
                    except FileNotFoundError:
                        event = None
                if event:
                    if not filter or filter.include(event):
                        yield event
                        num_results += 1
                        if limit and limit <= num_results:
                            return

    def get_event(self, id: int) -> Event:
        filename = self._get_filename_for_id(id, self.user_id)
        content = self.file_store.read(filename)
        data = json.loads(content)
        return event_from_dict(data)

    def get_latest_event(self) -> Event:
        return self.get_event(self.cur_id - 1)

    def get_latest_event_id(self) -> int:
        return self.cur_id - 1

    def filtered_events_by_source(self, source: EventSource) -> Iterable[Event]:
        for event in self.get_events():
            if event.source == source:
                yield event

    def _should_filter_event(
        self,
        event: Event,
        query: str | None = None,
        event_types: tuple[type[Event], ...] | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bool:
        """Check if an event should be filtered out based on the given criteria.

        Args:
            event: The event to check
            query: Text to search for in event content
            event_type: Filter by event type classes (e.g., (FileReadAction, ) ).
            source: Filter by event source
            start_date: Filter events after this date (ISO format)
            end_date: Filter events before this date (ISO format)

        Returns:
            bool: True if the event should be filtered out, False if it matches all criteria
        """
        if event_types and not isinstance(event, event_types):
            return True

        if source:
            if event.source is None or event.source.value != source:
                return True

        if start_date and event.timestamp is not None and event.timestamp < start_date:
            return True

        if end_date and event.timestamp is not None and event.timestamp > end_date:
            return True

        # Text search in event content if query provided
        if query:
            event_dict = event_to_dict(event)
            event_str = json.dumps(event_dict).lower()
            if query.lower() not in event_str:
                return True

        return False

    def get_matching_events(
        self,
        query: str | None = None,
        event_types: tuple[type[Event], ...] | None = None,
        source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        start_id: int = 0,
        limit: int = 100,
        reverse: bool = False,
    ) -> list[Event]:
        """Get matching events from the event stream based on filters.

        Args:
            query: Text to search for in event content
            event_types: Filter by event type classes (e.g., (FileReadAction, ) ).
            source: Filter by event source
            start_date: Filter events after this date (ISO format)
            end_date: Filter events before this date (ISO format)
            start_id: Starting ID in the event stream. Defaults to 0
            limit: Maximum number of events to return. Must be between 1 and 100. Defaults to 100
            reverse: Whether to retrieve events in reverse order. Defaults to False.

        Returns:
            list: List of matching events (as dicts)

        Raises:
            ValueError: If limit is less than 1 or greater than 100
        """
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')

        matching_events: list = []

        for event in self.get_events(start_id=start_id, reverse=reverse):
            if self._should_filter_event(
                event, query, event_types, source, start_date, end_date
            ):
                continue

            matching_events.append(event)

            # Stop if we have enough events
            if len(matching_events) >= limit:
                break

        return matching_events

    def get_events_by_action(
        self,
        actions: list[str],
        observations: list[str] | None = None,
        limit: int = 100,
        reverse: bool = True,
    ) -> list[Event]:
        """Get events filtered by specific actions with limit and sorting by created_at.

        Args:
            actions: List of action names to filter by (e.g., ['edit', 'finish'])
            limit: Maximum number of events to return. Must be between 1 and 100. Defaults to 100
            reverse: Whether to retrieve events in reverse order (newest first). Defaults to True

        Returns:
            list: List of matching events

        Raises:
            ValueError: If limit is less than 1 or greater than 100
        """
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')

        from openhands.core.config import load_app_config
        from openhands.storage.database import db_file_store

        config_app = load_app_config()

        if config_app.file_store == 'database':
            # Use database-specific filtering for better performance
            order_by = 'created_at DESC' if reverse else 'created_at ASC'
            events = db_file_store._get_events_by_action(
                self.sid, actions, limit, order_by, observations
            )
            return [event_from_dict(event_dict) for event_dict in events if event_dict]
        else:
            # Fallback to file-based filtering
            matching_events: list[Event] = []

            for event in self.get_events(reverse=reverse):
                event_dict = event_to_dict(event)
                event_action = event_dict.get('action')

                if event_action in actions:
                    matching_events.append(event)

                    # Stop if we have enough events
                    if len(matching_events) >= limit:
                        break

            return matching_events

    def _get_filename_for_id(self, id: int, user_id: str | None) -> str:
        return get_conversation_event_filename(self.sid, id, user_id)

    def _get_filename_for_cache(self, start: int, end: int) -> str:
        return f'{get_conversation_dir(self.sid, self.user_id)}event_cache/{start}-{end}.json'

    def _load_cache_page(self, start: int, end: int) -> _CachePage:
        """Read a page from the cache. Reading individual events is slow when there are a lot of them, so we use pages."""
        cache_filename = self._get_filename_for_cache(start, end)
        try:
            content = self.file_store.read(cache_filename)
            events = json.loads(content)
        except FileNotFoundError:
            events = None
        page = _CachePage(events, start, end)
        return page

    def _load_cache_page_for_index(self, index: int) -> _CachePage:
        offset = index % self.cache_size
        index -= offset
        return self._load_cache_page(index, index + self.cache_size)

    @staticmethod
    def _get_id_from_filename(filename: str) -> int:
        try:
            return int(filename.split('/')[-1].split('.')[0])
        except ValueError:
            logger.warning(f'get id from filename ({filename}) failed.')
            return -1
