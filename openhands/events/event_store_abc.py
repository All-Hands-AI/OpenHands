from abc import abstractmethod
from itertools import islice
from typing import Iterable

from deprecated import deprecated  # type: ignore

from openhands.events.event import Event, EventSource
from openhands.events.event_filter import EventFilter


class EventStoreABC:
    """A stored list of events backing a conversation."""

    sid: str
    user_id: str | None

    @abstractmethod
    def search_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter: EventFilter | None = None,
        limit: int | None = None,
    ) -> Iterable[Event]:
        """Retrieve events from the event stream, optionally excluding events using a filter.

        Args:
            start_id: The ID of the first event to retrieve. Defaults to 0.
            end_id: The ID of the last event to retrieve. Defaults to the last event in the stream.
            reverse: Whether to retrieve events in reverse order. Defaults to False.
            filter: An optional event filter

        Yields:
            Events from the stream that match the criteria.
        """

    @deprecated('Use search_events instead')
    def get_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter_out_type: tuple[type[Event], ...] | None = None,
        filter_hidden: bool = False,
    ) -> Iterable[Event]:
        yield from self.search_events(
            start_id,
            end_id,
            reverse,
            EventFilter(exclude_types=filter_out_type, exclude_hidden=filter_hidden),
        )

    @abstractmethod
    def get_event(self, id: int) -> Event:
        """Retrieve a single event from the event stream. Raise a FileNotFoundError if there was no such event."""

    @abstractmethod
    def get_latest_event(self) -> Event:
        """Get the latest event from the event stream."""

    @abstractmethod
    def get_latest_event_id(self) -> int:
        """Get the id of the latest event from the event stream."""

    @deprecated('use search_events instead')
    def filtered_events_by_source(self, source: EventSource) -> Iterable[Event]:
        yield from self.search_events(filter=EventFilter(source=source))

    @deprecated('use search_events instead')
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
        """
        if limit < 1 or limit > 100:
            raise ValueError('Limit must be between 1 and 100')

        events = self.search_events(
            start_id=start_id,
            reverse=reverse,
            filter=EventFilter(
                query=query,
                include_types=event_types,
                source=source,
                start_date=start_date,
                end_date=end_date,
            ),
        )
        return list(islice(events, limit))
