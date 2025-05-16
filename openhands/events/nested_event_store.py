import urllib
from dataclasses import dataclass
from typing import Iterable

import httpx  # type: ignore

from openhands.events.event import Event
from openhands.events.event_filter import EventFilter
from openhands.events.event_store_abc import EventStoreABC
from openhands.events.serialization.event import event_from_dict


@dataclass
class NestedEventStore(EventStoreABC):
    """
    A stored list of events backing a conversation
    """

    base_url: str
    sid: str
    user_id: str | None

    def search_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter: EventFilter | None = None,
        limit: int | None = None,
    ) -> Iterable[Event]:
        while True:
            search_params = urllib.urlencode(
                {
                    'start_id': start_id,
                    'reverse': reverse,
                    'limit': min(100, limit),
                }
            )
            url = f'{self.base_url}/events{search_params}'
            response = httpx.get(url)
            result_set = response.json()
            for result in result_set['results']:
                event = event_from_dict(result)
                start_id = event.id
                if end_id == event.id:
                    if not filter or filter.include(event):
                        yield event
                    return
                if filter and filter.exclude(event):
                    continue
                yield event
                limit -= 1
                if limit <= 0:
                    return
            if not result_set['has_more']:
                return

    def get_event(self, id: int) -> Event:
        events = list(self.search_events(start_id=id, limit=1))
        if not events:
            raise FileNotFoundError('no_event')
        return events[0]

    def get_latest_event(self) -> Event:
        events = list(self.search_events(reverse=True, limit=1))
        if not events:
            raise FileNotFoundError('no_event')
        return events[0]

    def get_latest_event_id(self) -> int:
        event = self.get_latest_event()
        return event.id if event else None
