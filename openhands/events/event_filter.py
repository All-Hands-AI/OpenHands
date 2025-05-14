import json
from dataclasses import dataclass

from duckdb import query

from openhands.events.event import Event
from openhands.events.serialization.event import event_to_dict


@dataclass
class EventFilter:
    exclude_hidden: bool = False
    query: str | None = None
    include_types: tuple[type[Event], ...] | None = None
    exclude_types: tuple[type[Event], ...] | None = None
    source: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def include(self, event: Event) -> bool:
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
            if query.lower() not in event_str:
                return False

        return True

    def exclude(self, event: Event):
        return not self.include(event)
