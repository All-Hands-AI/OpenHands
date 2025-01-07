from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

from litellm import supports_response_schema
from pydantic import BaseModel
from typing_extensions import override

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    CondenserConfig,
    LLMAttentionCondenserConfig,
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
    ObservationMaskingCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.events.observation import AgentCondensationObservation, Observation
from openhands.llm.llm import LLM

CONDENSER_METADATA_KEY = 'condenser_meta'
"""Key identifying where metadata is stored in a `State` object's `extra_data` field."""


def get_condensation_metadata(state: State) -> list[dict[str, Any]]:
    """Utility function to retrieve a list of metadata batches from a `State`.

    Args:
        state: The state to retrieve metadata from.

    Returns:
        list[dict[str, Any]]: A list of metadata batches, each representing a condensation.
    """
    if CONDENSER_METADATA_KEY in state.extra_data:
        return state.extra_data[CONDENSER_METADATA_KEY]
    return []


class Condenser(ABC):
    """Abstract condenser interface.

    Condensers take a list of `Event` objects and reduce them into a potentially smaller list.

    Agents can use condensers to reduce the amount of events they need to consider when deciding which action to take. To use a condenser, agents can call the `condensed_history` method on the current `State` being considered and use the results instead of the full history.

    Example usage::

        condenser = Condenser.from_config(condenser_config)
        events = condenser.condensed_history(state)
    """

    def __init__(self):
        self._metadata_batch: dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add information to the current metadata batch.

        Any key/value pairs added to the metadata batch will be recorded in the `State` at the end of the current condensation.

        Args:
            key: The key to store the metadata under.

            value: The metadata to store.
        """
        self._metadata_batch[key] = value

    def write_metadata(self, state: State) -> None:
        """Write the current batch of metadata to the `State`.

        Resets the current metadata batch: any metadata added after this call will be stored in a new batch and written to the `State` at the end of the next condensation.
        """
        if CONDENSER_METADATA_KEY not in state.extra_data:
            state.extra_data[CONDENSER_METADATA_KEY] = []
        if self._metadata_batch:
            state.extra_data[CONDENSER_METADATA_KEY].append(self._metadata_batch)

        # Since the batch has been written, clear it for the next condensation
        self._metadata_batch = {}

    @contextmanager
    def metadata_batch(self, state: State):
        """Context manager to ensure batched metadata is always written to the `State`."""
        try:
            yield
        finally:
            self.write_metadata(state)

    @abstractmethod
    def condense(self, events: list[Event]) -> list[Event]:
        """Condense a sequence of events into a potentially smaller list.

        New condenser strategies should override this method to implement their own condensation logic. Call `self.add_metadata` in the implementation to record any relevant per-condensation diagnostic information.

        Args:
            events: A list of events representing the entire history of the agent.

        Returns:
            list[Event]: An event sequence representing a condensed history of the agent.
        """

    def condensed_history(self, state: State) -> list[Event]:
        """Condense the state's history."""
        with self.metadata_batch(state):
            return self.condense(state.history)

    @classmethod
    def from_config(cls, config: CondenserConfig) -> Condenser:
        """Create a condenser from a configuration object.

        Args:
            config: Configuration for the condenser.

        Returns:
            Condenser: A condenser instance.

        Raises:
            ValueError: If the condenser type is not recognized.
        """
        match config:
            case NoOpCondenserConfig():
                return NoOpCondenser()

            case ObservationMaskingCondenserConfig():
                return ObservationMaskingCondenser(
                    **config.model_dump(exclude=['type'])
                )

            case RecentEventsCondenserConfig():
                return RecentEventsCondenser(**config.model_dump(exclude=['type']))

            case LLMSummarizingCondenserConfig(llm_config=llm_config):
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


class RollingCondenser(Condenser, ABC):
    """Base class for a specialized condenser strategy that applies condensation to a rolling history.

    The rolling history is computed by appending new events to the most recent condensation. For example, the sequence of calls::

        assert state.history == [event1, event2, event3]
        condensation = condenser.condensed_history(state)

        # ...new events are added to the state...

        assert state.history == [event1, event2, event3, event4, event5]
        condenser.condensed_history(state)

    will result in second call to `condensed_history` passing `condensation + [event4, event5]` to the `condense` method.
    """

    def __init__(self) -> None:
        self._condensation: list[Event] = []
        self._last_history_length: int = 0

        super().__init__()

    @override
    def condensed_history(self, state: State) -> list[Event]:
        new_events = state.history[self._last_history_length :]

        with self.metadata_batch(state):
            results = self.condense(self._condensation + new_events)

        self._condensation = results
        self._last_history_length = len(state.history)

        return results


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event]) -> list[Event]:
        """Returns the list of events unchanged."""
        return events


class ObservationMaskingCondenser(Condenser):
    """A condenser that masks the values of observations outside of a recent attention window."""

    def __init__(self, attention_window: int = 5):
        self.attention_window = attention_window

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """Replace the content of observations outside of the attention window with a placeholder."""
        results: list[Event] = []
        for i, event in enumerate(events):
            if (
                isinstance(event, Observation)
                and i < len(events) - self.attention_window
            ):
                results.append(AgentCondensationObservation('<MASKED>'))
            else:
                results.append(event)

        return results


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

            resp = self.llm.completion(
                messages=[{'content': summarize_prompt, 'role': 'user'}]
            )
            summary_response = resp.choices[0].message.content

            # Create a new summary event with the condensed content
            summary_event = AgentCondensationObservation(summary_response)

            # Add metrics to state
            self.add_metadata('response', resp.model_dump())
            self.add_metadata('metrics', self.llm.metrics.get())

            return [summary_event]

        except Exception as e:
            logger.error('Error condensing events: %s', str(e), exc_info=False)
            raise e


class AmortizedForgettingCondenser(RollingCondenser):
    """A condenser that maintains a condensed history and forgets old events when it grows too large."""

    def __init__(self, max_size: int = 100, keep_first: int = 0):
        """Initialize the condenser.

        Args:
            max_size: Maximum size of history before forgetting.
            keep_first: Number of initial events to always keep.

        Raises:
            ValueError: If keep_first is greater than max_size, keep_first is negative, or max_size is non-positive.
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
    """Utility class for the `LLMAttentionCondenser` that forces the LLM to return a list of integers."""

    ids: list[int]


class LLMAttentionCondenser(RollingCondenser):
    """Rolling condenser strategy that uses an LLM to select the most important events when condensing the history."""

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

        # This condenser relies on the `response_schema` feature, which is not supported by all LLMs
        if not supports_response_schema(
            model=self.llm.config.model,
            custom_llm_provider=self.llm.config.custom_llm_provider,
        ):
            raise ValueError(
                "The LLM model must support the 'response_schema' parameter to use the LLMAttentionCondenser."
            )

        super().__init__()

    def condense(self, events: list[Event]) -> list[Event]:
        """If the history is too long, use an LLM to select the most important events."""
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
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'ImportantEventSelection',
                    'schema': ImportantEventSelection.model_json_schema(),
                },
            },
        )

        response_ids = ImportantEventSelection.model_validate_json(
            response.choices[0].message.content
        ).ids

        self.add_metadata('all_event_ids', [event.id for event in events])
        self.add_metadata('response_ids', response_ids)
        self.add_metadata('metrics', self.llm.metrics.get())

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
