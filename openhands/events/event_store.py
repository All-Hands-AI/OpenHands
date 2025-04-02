import json
from dataclasses import dataclass
from typing import Iterable

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_from_dict, event_to_dict
from openhands.storage.files import FileStore
from openhands.storage.locations import (
    get_conversation_event_filename,
    get_conversation_events_dir,
)
from openhands.utils.shutdown_listener import should_continue


@dataclass
class EventStore:
    """
    A stored list of events backing a conversation
    """

    sid: str
    file_store: FileStore
    user_id: str | None
    cur_id: int = -1  # We fix this in post init if it is not specified

    def __post_init__(self) -> None:
        if self.cur_id >= 0:
            return
        events = []
        try:
            events_dir = get_conversation_events_dir(self.sid, self.user_id)
            events = self.file_store.list(events_dir)
        except FileNotFoundError:
            logger.debug(f'No events found for session {self.sid} at {events_dir}')

        if self.user_id:
            # During transition to new location, try old location if user_id is set
            # TODO: remove this code after 5/1/2025
            try:
                events_dir = get_conversation_events_dir(self.sid)
                events += self.file_store.list(events_dir)
            except FileNotFoundError:
                logger.debug(f'No events found for session {self.sid} at {events_dir}')

        if not events:
            self.cur_id = 0
            return

        # if we have events, we need to find the highest id to prepare for new events
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if id >= self.cur_id:
                self.cur_id = id + 1

    def get_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden: bool = False,
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

        def should_filter(event: Event) -> bool:
            if filter_hidden and hasattr(event, 'hidden') and event.hidden:
                return True
            if filter_out_type is not None and isinstance(event, filter_out_type):
                return True
            return False

        if reverse:
            if end_id is None:
                end_id = self.cur_id - 1
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
        filename = self._get_filename_for_id(id, self.user_id)
        try:
            content = self.file_store.read(filename)
            data = json.loads(content)
            return event_from_dict(data)
        except FileNotFoundError:
            logger.debug(f'File {filename} not found')
            # TODO remove this block after 5/1/2025
            if self.user_id:
                filename = self._get_filename_for_id(id, None)
                content = self.file_store.read(filename)
                data = json.loads(content)
                return event_from_dict(data)
            raise

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

    def _get_filename_for_id(self, id: int, user_id: str | None) -> str:
        return get_conversation_event_filename(self.sid, id, user_id)

    @staticmethod
    def _get_id_from_filename(filename: str) -> int:
        try:
            return int(filename.split('/')[-1].split('.')[0])
        except ValueError:
            logger.warning(f'get id from filename ({filename}) failed.')
            return -1
