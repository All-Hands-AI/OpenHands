from __future__ import annotations

from typing import overload

from pydantic import BaseModel

from openhands.events.action.agent import CondensationAction
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.events.observation.context_reorganization import (
    ContextReorganizationObservation,
)


class View(BaseModel):
    """Linearly ordered view of events.

    Produced by a condenser to indicate the included events are ready to process as LLM input.
    """

    events: list[Event]

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    # To preserve list-like indexing, we ideally support slicing and position-based indexing.
    # The only challenge with that is switching the return type based on the input type -- we
    # can mark the different signatures for MyPy with `@overload` decorators.

    @overload
    def __getitem__(self, key: slice) -> list[Event]: ...

    @overload
    def __getitem__(self, key: int) -> Event: ...

    def __getitem__(self, key: int | slice) -> Event | list[Event]:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            return [self[i] for i in range(start, stop, step)]
        elif isinstance(key, int):
            return self.events[key]
        else:
            raise ValueError(f'Invalid key type: {type(key)}')

    @staticmethod
    def from_events(events: list[Event]) -> View:
        """Create a view from a list of events, respecting the semantics of any condensation events."""
        forgotten_event_ids: set[int] = set()
        for event in events:
            if isinstance(event, CondensationAction):
                forgotten_event_ids.update(event.forgotten)

        kept_events = [event for event in events if event.id not in forgotten_event_ids]

        # If we have a summary, insert it at the specified offset.
        summary: str | None = None
        summary_offset: int | None = None
        context_reorganization_index: int | None = None

        # Process events to find the most recent condensation or context reorganization
        for i, event in enumerate(reversed(events)):
            # Handle CondensationAction
            if isinstance(event, CondensationAction):
                if event.summary is not None and event.summary_offset is not None:
                    summary = event.summary
                    summary_offset = event.summary_offset
                    break

            # Handle ContextReorganizationObservation
            elif isinstance(event, ContextReorganizationObservation):
                context_reorganization_index = len(events) - i - 1
                break

        # Handle context reorganization if available
        if context_reorganization_index is not None:
            # Create a new list with only the ContextReorganizationObservation and events after it
            new_events: list[Event] = []

            # Add the ContextReorganizationObservation
            new_events.append(events[context_reorganization_index])

            # Add only events that come after the context_reorganization_index
            for event in events[context_reorganization_index + 1 :]:
                if event.id not in forgotten_event_ids:
                    new_events.append(event)

            return View(events=new_events)

        # If no context reorganization, handle regular condensation summary if available
        if summary is not None and summary_offset is not None:
            kept_events.insert(
                summary_offset, AgentCondensationObservation(content=summary)
            )

        return View(events=kept_events)
