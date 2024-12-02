from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.condenser_config import (
    CondenserConfig,
    LLMCondenserConfig,
    NoOpCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.llm.llm import LLM


class Condenser(ABC):
    """Abstract condenser interface.

    Condensers take a list of events and reduce them into a potentially smaller list. Agents can use
    condensers to reduce the amount of events they need to consider when deciding which action to take.
    """

    @abstractmethod
    def condense(self, events: list[Event]) -> list[Event]:
        """Condense a list of events into a potentially smaller list.

        Args:
            events (List[Event]): List of events to condense.

        Returns:
            List[Event]: Condensed list of events.
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
            case RecentEventsCondenserConfig(max_events=max_events):
                return RecentEventsCondenser(max_events=max_events)
            case LLMCondenserConfig(llm_config=llm_config):
                return LLMCondenser(llm=LLM(config=llm_config))
            case _:
                raise ValueError(f'Unknown condenser type: {config.type}')


class NoOpCondenser(Condenser):
    """A condenser that does nothing to the event sequence."""

    def condense(self, events: list[Event]) -> list[Event]:
        """Returns the events list unchanged.

        Args:
            events (list[Event]): List of events to condense.

        Returns:
            list[Event]: The same list of events.
        """
        return events


class RecentEventsCondenser(Condenser):
    """A condenser that only keeps a certain number of the most recent events."""

    def __init__(self, max_events: int = 10):
        self.max_events = max_events

    def condense(self, events: list[Event]) -> list[Event]:
        """Keep only the most recent events (up to `max_events`).

        Args:
            events (list[Event]): List of events to condense.

        Returns:
            list[Event]: List containing only the most recent events.
        """
        return events[-self.max_events :]


class LLMCondenser(Condenser):
    """A condenser that relies on a language model to summarize the event sequence as a single event."""

    def __init__(self, llm: LLM):
        self.llm = llm

    def condense(self, events: list[Event]) -> list[Event]:
        """Attempts to condense the events by using a LLM.

        Args:
            events (list[Event]): List of events to condense.

        Returns:
            list[Event]: A list containing a single event summarizing the input sequence.

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
            summary_event = Event()
            setattr(summary_event, '_message', summary_response)
            setattr(summary_event, '_timestamp', events[-1].timestamp)
            setattr(summary_event, '_source', events[-1].source)

            return [summary_event]
        except Exception as e:
            logger.error('Error condensing events: %s', str(e), exc_info=False)
            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the memory chunk by chunk
            raise e
