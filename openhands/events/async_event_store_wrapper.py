import asyncio
from typing import Any, AsyncIterator, Iterable

from openhands.events.event import Event
from openhands.events.event_store import EventStore


class AsyncEventStoreWrapper:
    def __init__(self, event_store: EventStore, *args: Any, **kwargs: Any) -> None:
        self.event_store = event_store
        self.args = args
        self.kwargs = kwargs

    async def __aiter__(self) -> AsyncIterator[Event]:
        loop = asyncio.get_running_loop()

        # Define a helper function to run the synchronous get_events
        def _sync_get_events() -> Iterable[Event]:
            # This will perform the potentially blocking file read
            return self.event_store.get_events(*self.args, **self.kwargs)

        # Run the synchronous function in an executor thread
        events_iterable: Iterable[Event] = await loop.run_in_executor(None, _sync_get_events)

        # Now iterate asynchronously over the result (which is already in memory)
        for event in events_iterable:
             # Yield each event (no need for run_in_executor here anymore)
             yield event
             # Optional: Add a small sleep to allow other tasks to run if needed
             # await asyncio.sleep(0)
