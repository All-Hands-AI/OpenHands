import asyncio
from typing import Any, AsyncIterator

from openhands.events.event import Event
from openhands.events.event_store import EventStore


class AsyncEventStoreWrapper:
    def __init__(self, event_store: EventStore, *args: Any, **kwargs: Any) -> None:
        self.event_store = event_store
        self.args = args
        self.kwargs = kwargs

    async def __aiter__(self) -> AsyncIterator[Event]:
        loop = asyncio.get_running_loop()

        # Create an async generator that yields events
        for event in self.event_store.search_events(*self.args, **self.kwargs):
            # Run the blocking search_events() in a thread pool
            def get_event(e: Event = event) -> Event:
                return e

            yield await loop.run_in_executor(None, get_event)
