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
                if event.forgotten_event_ids is not None:
                    forgotten_event_ids.update(event.forgotten_event_ids)

        # Find the most recent context reorganization
        context_reorganization_index: int | None = None
        for i, event in enumerate(reversed(events)):
            if isinstance(event, ContextReorganizationObservation):
                context_reorganization_index = len(events) - i - 1
                break

        # Handle context reorganization if available
        if context_reorganization_index is not None:
            # Create a new list with only the ContextReorganizationObservation and events after it
            new_events: list[Event] = []

            # Add the ContextReorganizationObservation
            new_events.append(events[context_reorganization_index])

            # Find condensation actions that come after the context reorganization
            post_reorg_condensations = []
            for i, event in enumerate(events[context_reorganization_index + 1 :]):
                if (
                    isinstance(event, CondensationAction)
                    and event.summary is not None
                    and event.summary_offset is not None
                ):
                    post_reorg_condensations.append((i, event))

            # Process each condensation action
            for i, condensation in post_reorg_condensations:
                # Insert the condensation summary at the specified offset
                # Adjust the offset to be relative to the new_events list
                if (
                    condensation.summary is not None
                    and condensation.summary_offset is not None
                ):
                    offset = min(condensation.summary_offset, len(new_events))
                    new_events.insert(
                        offset,
                        AgentCondensationObservation(content=condensation.summary),
                    )

            # Add only events that come after the context_reorganization_index and are not forgotten
            for event in events[context_reorganization_index + 1 :]:
                if (
                    not isinstance(event, CondensationAction)
                    and event.id not in forgotten_event_ids
                ):
                    new_events.append(event)

            return View(events=new_events)

        # If no context reorganization, handle regular condensation
        kept_events = [
            event
            for event in events
            if event.id not in forgotten_event_ids
            and not isinstance(event, CondensationAction)
        ]

        # Find the most recent condensation action
        condensation_summary: str | None = None
        condensation_offset: int | None = None
        for event in reversed(events):
            if (
                isinstance(event, CondensationAction)
                and event.summary is not None
                and event.summary_offset is not None
            ):
                condensation_summary = event.summary
                condensation_offset = event.summary_offset
                break

        # Insert the condensation summary if available
        if condensation_summary is not None and condensation_offset is not None:
            # Ensure offset is a valid integer
            offset_value = min(condensation_offset, len(kept_events))
            kept_events.insert(
                offset_value, AgentCondensationObservation(content=condensation_summary)
            )

        return View(events=kept_events)
