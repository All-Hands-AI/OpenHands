from abc import ABC, abstractmethod
from typing import List

from openhands.core.logger import openhands_logger as logger
from openhands.events.event import Event
from openhands.llm.llm import LLM
from openhands.memory.condenser_config import (
    CondenserConfig,
    NoopCondenserConfig,
    RecentEventsCondenserConfig,
    LLMCondenserConfig,
)


class Condenser(ABC):
    @abstractmethod
    def condense(self, events: List[Event]) -> List[Event]:
        """Condense a list of events into a potentially smaller list.

        Parameters:
        - events (List[Event]): List of events to condense

        Returns:
        - List[Event]: Condensed list of events
        """
        pass

    @classmethod
    def from_config(cls, config: CondenserConfig) -> 'Condenser':
        """Create a condenser from a configuration object.

        Parameters:
        - config (CondenserConfig): Configuration for the condenser

        Returns:
        - Condenser: A condenser instance

        Raises:
        - ValueError: If the condenser type is not recognized
        """
        if config.type == "noop":
            return NoopCondenser()
        elif config.type == "recent":
            return RecentEventsCondenser(max_events=config.max_events)
        elif config.type == "llm":
            return LLMCondenser(llm=LLM(config=config.llm_config))
        else:
            raise ValueError(f"Unknown condenser type: {config.type}")


class NoopCondenser(Condenser):
    def condense(self, events: List[Event]) -> List[Event]:
        """Returns the events list unchanged.

        Parameters:
        - events (List[Event]): List of events to condense

        Returns:
        - List[Event]: The same list of events
        """
        return events


class RecentEventsCondenser(Condenser):
    def __init__(self, max_events: int = 10):
        self.max_events = max_events

    def condense(self, events: List[Event]) -> List[Event]:
        """Keep only the most recent events up to max_events.

        Parameters:
        - events (List[Event]): List of events to condense

        Returns:
        - List[Event]: List containing only the most recent events
        """
        return events[-self.max_events:]


class LLMCondenser(Condenser):
    def __init__(self, llm: LLM):
        self.llm = llm

    def condense(self, events: List[Event]) -> List[Event]:
        """Attempts to condense the events by using the llm.

        Parameters:
        - events (List[Event]): List of events to condense

        Returns:
        - List[Event]: Condensed list of events

        Raises:
        - Exception: the same exception as it got from the llm or processing the response
        """
        try:
            # Convert events to a format suitable for summarization
            events_text = "\n".join(f"{e.timestamp}: {e.message}" for e in events)
            summarize_prompt = f"Please summarize these events:\n{events_text}"
            
            messages = [{'content': summarize_prompt, 'role': 'user'}]
            resp = self.llm.completion(messages=messages)
            summary_response = resp['choices'][0]['message']['content']
            
            # Create a new summary event with the condensed content
            summary_event = Event()
            summary_event._message = summary_response
            summary_event._timestamp = events[-1].timestamp
            summary_event._source = events[-1].source
            
            return [summary_event]
        except Exception as e:
            logger.error('Error condensing events: %s', str(e), exc_info=False)
            # TODO If the llm fails with ContextWindowExceededError, we can try to condense the memory chunk by chunk
            raise
