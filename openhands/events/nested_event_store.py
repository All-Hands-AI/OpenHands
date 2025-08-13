from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlencode

import httpx  # type: ignore
from fastapi import status

from openhands.events.event import Event
from openhands.events.event_filter import EventFilter
from openhands.events.event_store_abc import EventStoreABC
from openhands.events.serialization.event import event_from_dict


@dataclass
class NestedEventStore(EventStoreABC):
    """A stored list of events backing a conversation."""

    base_url: str
    sid: str
    user_id: str | None
    session_api_key: str | None = None

    def search_events(
        self,
        start_id: int = 0,
        end_id: int | None = None,
        reverse: bool = False,
        filter: EventFilter | None = None,
        limit: int | None = None,
    ) -> Iterable[Event]:
        while True:
            search_params = {
                'start_id': start_id,
                'reverse': reverse,
            }
            if limit is not None:
                search_params['limit'] = min(100, limit)
            search_str = urlencode(search_params)
            url = f'{self.base_url}/events?{search_str}'
            headers = {}
            if self.session_api_key:
                headers['X-Session-API-Key'] = self.session_api_key
            response = httpx.get(url, headers=headers)
            if response.status_code == status.HTTP_404_NOT_FOUND:
                # Follow pattern of event store not throwing errors on not found
                return
            result_set = response.json()
            for result in result_set['events']:
                event = event_from_dict(result)
                start_id = max(start_id, event.id + 1)
                if end_id == event.id:
                    if not filter or filter.include(event):
                        yield event
                    return
                if filter and filter.exclude(event):
                    continue
                yield event
                if limit is not None:
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
        return event.id
