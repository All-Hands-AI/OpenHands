from __future__ import annotations

from typing import overload

from pydantic import BaseModel

from openhands.events.action.agent import (
    CondensationAction,
    ContextReorganizationAction,
)
from openhands.events.event import Event
from openhands.events.observation.agent import AgentCondensationObservation


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
        new_events: list[Event] = []

        for i, event in enumerate(events):
            if isinstance(event, CondensationAction):
                new_events = View._condense(event, new_events)
            elif isinstance(event, ContextReorganizationAction):
                new_events = [event]
            else:
                new_events.append(event)

        return View(events=new_events)

    @staticmethod
    def _condense(
        condensation_action: CondensationAction, events: list[Event]
    ) -> list[Event]:
        """Condense the events based on the condensation action."""

        # only keep events that are not forgotten
        if condensation_action.forgotten_event_ids is None:
            new_events = events
        else:
            new_events = [
                e for e in events if e.id not in condensation_action.forgotten_event_ids
            ]

        new_events += [condensation_action]

        # create AgentCondensationObservation is we have a summary
        if condensation_action.summary is not None:
            condensation_observation = AgentCondensationObservation(
                content=condensation_action.summary
            )
            if condensation_action.summary_offset is not None:
                offset_value = min(condensation_action.summary_offset, len(new_events))
                new_events.insert(offset_value, condensation_observation)
            else:
                new_events.append(condensation_observation)

        return new_events
