from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    CondenserConfig,
    LLMAttentionCondenserConfig,
    LLMCondenserConfig,
    NoOpCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import ObservationType
from openhands.events.event import Event
from openhands.events.observation import Observation
from openhands.llm.llm import LLM

CONDENSER_METADATA_KEY = 'condenser_meta'
"""The key identifying where metadata is stored in a state's extra_data."""


def get_condensation_metadata(state: State) -> list[Any]:
    if CONDENSER_METADATA_KEY in state.extra_data:
        return state.extra_data[CONDENSER_METADATA_KEY]
    return []


class Condenser(ABC):
    """Abstract condenser interface.

    Condensers take a list of events and reduce them into a potentially smaller list. Agents can use condensers to reduce the amount of events they need to consider when deciding which action to take.
    """

    def __init__(self):
        self._metadata_batch: dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Record metadata about the current condensation.

        Args:
            key (str): The key to store the metadata under.

            value (Any): The metadata to store.
        """
        self._metadata_batch[key] = value

    def write_metadata(self, state: State) -> None:
        """Write the current batch of metadata to the state."""
        if CONDENSER_METADATA_KEY not in state.extra_data:
            state.extra_data[CONDENSER_METADATA_KEY] = []
        if self._metadata_batch:
            state.extra_data[CONDENSER_METADATA_KEY].append(self._metadata_batch)

    def reset_metadata(self) -> None:
        """Reset the metadata batch."""
        self._metadata_batch = {}

    @contextmanager
    def metadata_batch(self, state: State):
        """Context manager to ensure batched metadata is always written."""
        try:
            yield
        finally:
            self.write_metadata(state)
            self.reset_metadata()

    @abstractmethod
    def condense(self, events: list[Event]) -> list[Event]:
        """Condense a sequence of events into a potentially smaller list.

        Args:
            events (list[Event]): A list of events to be condensed.

        Returns:
            list[Event]: The condensed event sequence.
        """
        pass

    def condensed_history(self, state: State) -> list[Event]:
        """Condense the state's history into a potentially smaller list."""
        with self.metadata_batch(state):
            return self.condense(state.history)

    @classmethod
    def from_config(cls, config: CondenserConfig) -> Condenser:
        """Create a condenser from a configuration object.

        Args:
            config (CondenserConfig): Configuration for the condenser.

        Returns:
            Condenser: A condenser instance.

        Raises:
            ValueError: If the condenser type is not recognized.
        """
        match config:
            case NoOpCondenserConfig():
                return NoOpCondenser()
            case RecentEventsCondenserConfig():
                return RecentEventsCondenser(**config.model_dump(exclude=['type']))
            case LLMCondenserConfig(llm_config=llm_config):
                return LLMSummarizingCondenser(llm=LLM(config=llm_config))
            case AmortizedForgettingCondenserConfig():
                return AmortizedForgettingCondenser(
                    **config.model_dump(exclude=['type'])
                )
            case LLMAttentionCondenserConfig(llm_config=llm_config):
                return LLMAttentionCondenser(
                    llm=LLM(config=llm_config),
                    **config.model_dump(exclude=['type', 'llm_config']),
                )
            case _:
                raise ValueError(f'Unknown condenser config: {config}')


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event]) -> list[Event]:
        """Returns the list of events unchanged."""
        return events


class RecentEventsCondenser(Condenser):
    """A condenser that only keeps a certain number of the most recent events."""

    def __init__(self, keep_first: int = 0, max_events: int = 10):
        self.keep_first = keep_first
        self.max_events = max_events

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Keep only the most recent events (up to `max_events`)."""
        head = events[: self.keep_first]
        tail_length = max(0, self.max_events - len(head))
        tail = events[-tail_length:]
        return head + tail


@dataclass
class CondensationObservation(Observation):
    """Represents the output of a condensation action."""

    observation: str = ObservationType.RUN

    @property
    def message(self) -> str:
        return self.content


class LLMSummarizingCondenser(Condenser):
    """A condenser that relies on a language model to summarize the event sequence as a single event."""

    def __init__(self, llm: LLM):
        self.llm = llm

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Applies an LLM to summarize the list of events.

        Raises:
            Exception: If the LLM is unable to summarize the event sequence.
        """
        try:
            # Convert events to a format suitable for summarization
            events_text = '\n'.join(f'{e.timestamp}: {e.message}' for e in events)
            summarize_prompt = f'Please summarize these events:\n{events_text}'

            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = self.llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']

            # Create a new summary event with the condensed content
            summary_event = CondensationObservation(summary_response)

            # Add metrics to state
            self.add_metadata('response', resp.model_dump())
            self.add_metadata('metrics', self.llm.metrics.get())

            return [summary_event]

        except Exception as e:
            logger.error('Error condensing events: %s', str(e), exc_info=False)
            raise e


class RollingCondenser(Condenser, ABC):
    """Base class for a specialized condenser strategy that applies condensation to a rolling history containing the old condensation and new values."""

    def __init__(self) -> None:
        self._condensation: list[Event] = []
        self._last_history_length: int = 0

        super().__init__()

    def condensed_history(self, state: State) -> list[Event]:
        """Condense the state's history into a potentially smaller list."""
        new_events = state.history[self._last_history_length :]

        with self.metadata_batch(state):
            results = self.condense(self._condensation + new_events)

        self._condensation = results
        self._last_history_length = len(state.history)

        return results


class AmortizedForgettingCondenser(RollingCondenser):
    """A condenser that maintains a condensed history and forgets old events when it grows too large."""

    def __init__(self, max_size: int = 100, keep_first: int = 0):
        """Initialize the condenser.

        Args:
            max_size (int, optional): Maximum size of history before forgetting. Defaults to 100.
            keep_first (int, optional): Number of initial events to always keep. Defaults to 0.

        Raises:
            ValueError: If keep_first is greater than max_size, keep_first is negative, or max_size is
            non-positive.
        """
        if keep_first >= max_size // 2:
            raise ValueError(
                f'keep_first ({keep_first}) must be less than half of max_size ({max_size})'
            )
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')
        if max_size < 1:
            raise ValueError(f'max_size ({keep_first}) cannot be non-positive')

        self.max_size = max_size
        self.keep_first = keep_first

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Apply the amortized forgetting strategy to the given list of events."""
        if len(events) <= self.max_size:
            return events

        target_size = self.max_size // 2
        head = events[: self.keep_first]

        events_from_tail = target_size - len(head)
        tail = events[-events_from_tail:]

        return head + tail


class ImportantEventSelection(BaseModel):
    ids: list[int]


class LLMAttentionCondenser(RollingCondenser):
    def __init__(self, llm: LLM, max_size: int = 100, keep_first: int = 0):
        if keep_first >= max_size // 2:
            raise ValueError(
                f'keep_first ({keep_first}) must be less than half of max_size ({max_size})'
            )
        if keep_first < 0:
            raise ValueError(f'keep_first ({keep_first}) cannot be negative')
        if max_size < 1:
            raise ValueError(f'max_size ({keep_first}) cannot be non-positive')

        self.max_size = max_size
        self.keep_first = keep_first
        self.llm = llm

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        if len(events) <= self.max_size:
            return events

        target_size = self.max_size // 2
        head = events[: self.keep_first]

        events_from_tail = target_size - len(head)

        message: str = """You will be given a list of actions, observations, and thoughts from a coding agent.
        Each item in the list has an identifier. Please sort the identifiers in order of how important the
        contents of the item are for the next step of the coding agent's task, from most important to least
        important."""

        response = self.llm.completion(
            messages=[
                {'content': message, 'role': 'user'},
                *[
                    {
                        'content': f'<ID>{e.id}</ID>\n<CONTENT>{e.message}</CONTENT>',
                        'role': 'user',
                    }
                    for e in events
                ],
            ],
            response_format=ImportantEventSelection,
        )

        response_ids = response.choices[0].message.content.ids

        self.add_metadata('all_event_ids', [event.id for event in events])
        self.add_metadata('response_ids', response_ids)

        # Filter out any IDs from the head and trim the results down
        head_ids = [event.id for event in head]
        response_ids = [
            response_id for response_id in response_ids if response_id not in head_ids
        ][:events_from_tail]

        # If the response IDs aren't _long_ enough, iterate backwards through the events and add any unfound IDs to the list.
        for event in reversed(events):
            if len(response_ids) >= events_from_tail:
                break
            if event.id not in response_ids:
                response_ids.append(event.id)

        # Grab the events associated with the response IDs
        tail = [event for event in events if event.id in response_ids]

        return head + tail
