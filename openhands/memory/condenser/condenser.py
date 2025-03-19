from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

from typing_extensions import override

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import CondenserConfig
from openhands.events.event import Event

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


CONDENSER_REGISTRY: dict[type[CondenserConfig], type[Condenser]] = {}
"""Registry of condenser configurations to their corresponding condenser classes."""


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
    def register_config(cls, configuration_type: type[CondenserConfig]) -> None:
        """Register a new condenser configuration type.

        Instances of registered configuration types can be passed to `from_config` to create instances of the corresponding condenser.

        Args:
            configuration_type: The type of configuration used to create instances of the condenser.

        Raises:
            ValueError: If the configuration type is already registered.
        """
        if configuration_type in CONDENSER_REGISTRY:
            raise ValueError(
                f'Condenser configuration {configuration_type} is already registered'
            )
        CONDENSER_REGISTRY[configuration_type] = cls

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
        try:
            condenser_class = CONDENSER_REGISTRY[type(config)]
            return condenser_class.from_config(config)
        except KeyError:
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
    
    Attributes:
        _condensation: A list of Event objects representing the result of the previous condensation.
            This is used to avoid reprocessing the entire history on each call to condensed_history.
            When a condensation occurs, this list will contain any AgentCondensationAction objects
            that summarize previously condensed events.
            
        _last_history_length: An integer tracking the length of state.history at the time of the
            last condensation. This is used to identify new events that have been added since the
            last condensation and to detect if the history has been truncated.
            
    Note:
        These tracking variables can be reconstructed from the state history by examining
        AgentCondensationAction objects and their positions in the history. This is useful
        for debugging or understanding the condenser's state at any point in time.
    """

    def __init__(self) -> None:
        self._condensation: list[Event] = []
        self._last_history_length: int = 0

        super().__init__()
        
    def reset_tracking(self) -> None:
        """Reset the tracking variables to their initial state.
        
        This forces the condenser to process the entire history on the next call
        to condensed_history, rather than just the new events.
        """
        self._condensation = []
        self._last_history_length = 0

    @override
    def condensed_history(self, state: State) -> list[Event]:
        # The history should grow monotonically -- if it doesn't, something has
        # truncated the history and we need to reset our tracking.
        if len(state.history) < self._last_history_length:
            # Reset tracking variables if history has been truncated
            self.reset_tracking()

        # Extract only the new events that have been added since the last condensation
        # This is an optimization to avoid reprocessing the entire history
        new_events = state.history[self._last_history_length :]

        with self.metadata_batch(state):
            # Combine the previous condensation result with new events
            # This allows incremental processing of the history
            results = self.condense(self._condensation + new_events)

        # Store the condensation result for the next call
        self._condensation = results
        # Update the history length tracker to the current length
        self._last_history_length = len(state.history)

        return results
        
    def reconstruct_tracking_variables(self, state: State) -> tuple[list[Event], int]:
        """Reconstruct the tracking variables from the state history.
        
        This method analyzes the state history to reconstruct what the _condensation and
        _last_history_length variables would be if the condenser had processed this state.
        This is useful for debugging or understanding the condenser's state.
        
        Args:
            state: The state containing the history to analyze.
            
        Returns:
            A tuple containing:
                - The reconstructed _condensation list
                - The reconstructed _last_history_length value
                
        Note:
            This method does not modify the condenser's actual tracking variables.
            It only returns what they would be based on the given state.
        """
        from openhands.events.action.agent import AgentCondensationAction
        
        # If there are no condensation actions in the history, the condensation
        # would be the entire history and the last_history_length would be the
        # current history length
        condensation_actions = [
            (i, event) for i, event in enumerate(state.history) 
            if isinstance(event, AgentCondensationAction)
        ]
        
        if not condensation_actions:
            return state.history.copy(), len(state.history)
            
        # Find the most recent condensation action
        last_condensation_idx, last_condensation = condensation_actions[-1]
        
        # The condensation would be all events up to and including the last condensation action
        reconstructed_condensation = state.history[:last_condensation_idx + 1].copy()
        
        # The last_history_length would be the current history length
        reconstructed_last_history_length = len(state.history)
        
        return reconstructed_condensation, reconstructed_last_history_length
