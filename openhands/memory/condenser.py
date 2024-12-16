from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    CondenserConfig,
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


def get_condensation_metadata(state: State) -> list[dict[str, Any]]:
    if CONDENSER_METADATA_KEY in state.extra_data:
        return state.extra_data[CONDENSER_METADATA_KEY]
    return []


class Condenser(ABC):
    """Abstract condenser interface.

    Condensers take a list of events and reduce them into a potentially smaller list. Agents can use
    condensers to reduce the amount of events they need to consider when deciding which action to take.
    """

    @abstractmethod
    def condense(self, state: State) -> list[Event]:
        """Condense the state's history into a potentially smaller list.

        Args:
            state (State): The state containing the event history to condense.

        Returns:
            list[Event]: The condensed event sequence.
        """
        pass

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
                return LLMCondenser(llm=LLM(config=llm_config))
            case AmortizedForgettingCondenserConfig():
                return AmortizedForgettingCondenser(**config.model_dump(exclude=['type']))
            case _:
                raise ValueError(f'Unknown condenser config: {config}')


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, state: State) -> list[Event]:
        """Returns the state's history unchanged.

        Args:
            state (State): The state containing the event history to condense.
        """
        return state.history


class RecentEventsCondenser(Condenser):
    """A condenser that only keeps a certain number of the most recent events."""

    def __init__(self, keep_first: int = 0, max_events: int = 10):
        self.keep_first = keep_first
        self.max_events = max_events

    def condense(self, state: State) -> list[Event]:
        """Keep only the most recent events (up to `max_events`).

        Args:
            state (State): The state containing the event history to condense.
        """
        events = state.history
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


class LLMCondenser(Condenser):
    """A condenser that relies on a language model to summarize the event sequence as a single event."""

    def __init__(self, llm: LLM):
        self.llm = llm

    def condense(self, state: State) -> list[Event]:
        """Attempts to condense the state's history by using a LLM.

        Args:
            state (State): The state containing the event history to condense.

        Raises:
            Exception: If the LLM is unable to summarize the event sequence.
        """
        try:
            # Convert events to a format suitable for summarization
            events_text = '\n'.join(f'{e.timestamp}: {e.message}' for e in state.history)
            summarize_prompt = f'Please summarize these events:\n{events_text}'

            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = self.llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']

            # Create a new summary event with the condensed content
            summary_event = CondensationObservation(summary_response)

            # Add metrics to state
            if CONDENSER_METADATA_KEY not in state.extra_data:
                state.extra_data[CONDENSER_METADATA_KEY] = []
            state.extra_data[CONDENSER_METADATA_KEY].append({
                'response': resp.model_dump(),
                'metrics': self.llm.metrics.get(),
            })

            return [summary_event]

        except Exception as e:
            logger.error('Error condensing events: %s', str(e), exc_info=False)
            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the memory chunk by chunk
            raise e


class AmortizedForgettingCondenser(Condenser):
    """A condenser that maintains a condensed history and forgets old events when it grows too large."""

    def __init__(self, max_size: int = 100, keep_first: int = 0):
        """Initialize the condenser.

        Args:
            max_size (int, optional): Maximum size of history before forgetting. Defaults to 100.
            keep_first (int, optional): Number of initial events to always keep. Defaults to 0.

        Raises:
            ValueError: If keep_first is greater than max_size.
        """
        if keep_first > max_size:
            raise ValueError(f"keep_first ({keep_first}) cannot be greater than max_size ({max_size})")
        self.max_size = max_size
        self.keep_first = keep_first
        self._condensed_history: list[Event] = []

    def condense(self, state: State) -> list[Event]:
        """Maintain a condensed history by adding new events and forgetting old ones when needed.

        Args:
            state (State): The state containing the event history to condense.

        Returns:
            list[Event]: The current condensed event sequence.
        """
        # Initialize or get the condenser metadata list
        if CONDENSER_METADATA_KEY not in state.extra_data:
            state.extra_data[CONDENSER_METADATA_KEY] = []

        # Track changes for this condensation
        changes = {
            'added_events': [],
            'removed_events': []
        }

        # If we have no history yet, initialize with all events
        if not self._condensed_history:
            self._condensed_history = state.history.copy()
            changes['added_events'] = [e.id for e in self._condensed_history]

            # Apply forgetting logic immediately if needed
            while len(self._condensed_history) > self.max_size:
                # Calculate how many events we can forget
                forgettable_events = self._condensed_history[self.keep_first:]
                if not forgettable_events:  # If all events are protected by keep_first
                    break

                # Forget half of the forgettable events
                forget_count = len(forgettable_events) // 2
                forgotten_events = self._condensed_history[self.keep_first:self.keep_first + forget_count]
                changes['removed_events'].extend(e.id for e in forgotten_events)

                self._condensed_history = (
                    self._condensed_history[:self.keep_first] +
                    self._condensed_history[self.keep_first + forget_count:]
                )
        else:
            # Find the timestamp of our last event
            last_timestamp = self._condensed_history[-1].timestamp

            # Add any new events that occurred after our last event
            new_events = [e for e in state.history if e.timestamp > last_timestamp]
            changes['added_events'] = [e.id for e in new_events]
            self._condensed_history.extend(new_events)

            # If we're over max_size, forget events while preserving keep_first
            while len(self._condensed_history) > self.max_size:
                # Calculate how many events we can forget
                forgettable_events = self._condensed_history[self.keep_first:]
                if not forgettable_events:  # If all events are protected by keep_first
                    break

                # Forget half of the forgettable events
                forget_count = len(forgettable_events) // 2
                forgotten_events = self._condensed_history[self.keep_first:self.keep_first + forget_count]
                changes['removed_events'].extend(e.id for e in forgotten_events)

                self._condensed_history = (
                    self._condensed_history[:self.keep_first] +
                    self._condensed_history[self.keep_first + forget_count:]
                )

        # Record changes in state metadata if any changes occurred
        if changes['added_events'] or changes['removed_events']:
            state.extra_data[CONDENSER_METADATA_KEY].append(changes)

        return self._condensed_history
