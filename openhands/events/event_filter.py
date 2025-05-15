import json
from dataclasses import dataclass

from openhands.events.event import Event
from openhands.events.serialization.event import event_to_dict


@dataclass
class EventFilter:
    """A filter for Event objects in the event stream.

    EventFilter provides a flexible way to filter events based on various criteria
    such as event type, source, date range, and content. It can be used to include
    or exclude events from search results based on the specified criteria.

    Attributes:
        exclude_hidden: Whether to exclude events marked as hidden. Defaults to False.
        query: Text string to search for in event content. Case-insensitive. Defaults to None.
        include_types: Tuple of Event types to include. Only events of these types will pass the filter.
            Defaults to None (include all types).
        exclude_types: Tuple of Event types to exclude. Events of these types will be filtered out.
            Defaults to None (exclude no types).
        source: Filter by event source (e.g., 'agent', 'user', 'environment'). Defaults to None.
        start_date: ISO format date string. Only events after this date will pass the filter.
            Defaults to None.
        end_date: ISO format date string. Only events before this date will pass the filter.
            Defaults to None.
    """

    exclude_hidden: bool = False
    query: str | None = None
    include_types: tuple[type[Event], ...] | None = None
    exclude_types: tuple[type[Event], ...] | None = None
    source: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def include(self, event: Event) -> bool:
        """Determine if an event should be included based on the filter criteria.

        This method checks if the given event matches all the filter criteria.
        If any criterion fails, the event is excluded.

        Args:
            event: The Event object to check against the filter criteria.

        Returns:
            bool: True if the event passes all filter criteria and should be included,
                  False otherwise.
        """
        if self.include_types and not isinstance(event, self.include_types):
            return False

        if self.exclude_types is not None and isinstance(event, self.exclude_types):
            return False

        if self.source:
            if event.source is None or event.source.value != self.source:
                return False

        if (
            self.start_date
            and event.timestamp is not None
            and event.timestamp < self.start_date
        ):
            return False

        if (
            self.end_date
            and event.timestamp is not None
            and event.timestamp > self.end_date
        ):
            return False

        if self.exclude_hidden and getattr(event, 'hidden', False):
            return False

        # Text search in event content if query provided
        if self.query:
            event_dict = event_to_dict(event)
            event_str = json.dumps(event_dict).lower()
            if self.query.lower() not in event_str:
                return False

        return True

    def exclude(self, event: Event) -> bool:
        """Determine if an event should be excluded based on the filter criteria.

        This is the inverse of the include method.

        Args:
            event: The Event object to check against the filter criteria.

        Returns:
            bool: True if the event should be excluded, False if it should be included.
        """
        return not self.include(event)
