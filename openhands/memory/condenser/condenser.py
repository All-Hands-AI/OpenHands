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
            
    def get_condensation_action(self, state: State) -> Event | None:
        """Get the condensation action if condensation is needed, or None if not.
        
        This method is used for persistence in the event stream. It should return an
        AgentCondensationAction if condensation occurred, or None if no condensation was needed.
        
        Args:
            state: The state containing the history to condense.
            
        Returns:
            Event | None: An AgentCondensationAction if condensation occurred, or None if not.
        """
        # Default implementation returns None (no condensation)
        return None

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
        These tracking variables are automatically reconstructed from the state history when
        the condenser is initialized with an existing history containing AgentCondensationAction
        events. This ensures that the condenser can properly resume operation after an application
        restart without losing context. The reconstruction process examines the most recent
        AgentCondensationAction in the history and uses it to rebuild the internal state.
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
        """Condense the state's history into a list of events.
        
        This method reconstructs the internal tracking state if needed, then
        processes the history to produce a condensed version.
        
        Args:
            state: The state containing the history to condense.
            
        Returns:
            list[Event]: A condensed version of the state history.
        """
        from openhands.events.action.agent import AgentCondensationAction
        
        # If we're loading a fresh instance but have history, try to reconstruct state
        if not self._condensation and self._last_history_length == 0 and state.history:
            self._reconstruct_state_from_history(state)
        
        # The history should grow monotonically -- if it doesn't, something has
        # truncated the history and we need to reset our tracking.
        if len(state.history) < self._last_history_length:
            # Reset tracking variables if history has been truncated
            self.reset_tracking()

        # Extract only the new events that have been added since the last condensation
        # This is an optimization to avoid reprocessing the entire history
        new_events = state.history[self._last_history_length:]

        with self.metadata_batch(state):
            # Combine the previous condensation result with new events
            # This allows incremental processing of the history
            results = self.condense(self._condensation + new_events)

        # Store the condensation result for the next call
        self._condensation = results
        # Update the history length tracker to the current length
        self._last_history_length = len(state.history)

        return results
        
    def _reconstruct_state_from_history(self, state: State) -> None:
        """Reconstruct the internal tracking state from the history.
        
        This method is called when a fresh instance is loaded with existing history.
        It attempts to find the most recent AgentCondensationAction in the history
        and use it to reconstruct the internal tracking state.
        
        Args:
            state: The state containing the history to analyze.
        """
        from openhands.events.action.agent import AgentCondensationAction
        
        # Find the most recent AgentCondensationAction
        condensation_action = None
        for event in reversed(state.history):
            if isinstance(event, AgentCondensationAction):
                condensation_action = event
                break
                
        if condensation_action is not None:
            # Find where in the history we left off
            last_processed_index = 0
            for i, e in enumerate(state.history):
                if hasattr(e, 'id') and e.id == condensation_action.end_id:
                    last_processed_index = i + 1
                    break
            
            # Reconstruct the condensation result based on the condenser's structure
            # For LLMSummarizingCondenser, this would be head + condensation_action
            head = state.history[:min(self.keep_first, len(state.history))] if hasattr(self, 'keep_first') else []
            self._condensation = head + [condensation_action]
            self._last_history_length = last_processed_index
            
    @override
    def get_condensation_action(self, state: State) -> Event | None:
        """Get the condensation action if condensation is needed, or None if not.
        
        This method first reconstructs the internal tracking state if needed, then
        determines if condensation is needed based on the current state history.
        If condensation is needed, it returns the AgentCondensationAction that would
        be created. Otherwise, it returns None.
        
        Args:
            state: The state containing the history to analyze.
            
        Returns:
            Event | None: An AgentCondensationAction if condensation occurred, or None if not.
        """
        from openhands.events.action.agent import AgentCondensationAction
        
        # If we're loading a fresh instance but have history, try to reconstruct state
        if not self._condensation and self._last_history_length == 0 and state.history:
            self._reconstruct_state_from_history(state)
        
        # The history should grow monotonically -- if it doesn't, something has
        # truncated the history and we need to reset our tracking.
        if len(state.history) < self._last_history_length:
            # Reset tracking variables if history has been truncated
            self.reset_tracking()

        # Extract only the new events that have been added since the last condensation
        new_events = state.history[self._last_history_length:]

        # Combine the previous condensation result with new events
        combined_events = self._condensation + new_events
        
        # Check if condensation is needed by comparing the result of condense() with the combined events
        with self.metadata_batch(state):
            condensed_events = self.condense(combined_events)
        
        # If the condensed events are different from the combined events, condensation occurred
        if len(condensed_events) != len(combined_events):
            # Find the AgentCondensationAction in the condensed events
            for event in condensed_events:
                if isinstance(event, AgentCondensationAction):
                    # Update our internal state to match what would happen in condensed_history()
                    self._condensation = condensed_events
                    self._last_history_length = len(state.history)
                    return event
        
        # No condensation occurred
        return None
        
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
        
        # Find the most recent AgentCondensationAction
        condensation_action = None
        for event in reversed(state.history):
            if isinstance(event, AgentCondensationAction):
                condensation_action = event
                break
                
        if condensation_action is None:
            # No condensation has occurred yet
            return [], 0
            
        # Find where in the history we left off
        last_processed_index = 0
        for i, event in enumerate(state.history):
            if hasattr(event, 'id') and event.id == condensation_action.end_id:
                last_processed_index = i + 1
                break
        
        # Reconstruct the condensation result based on the condenser's structure
        # For LLMSummarizingCondenser, this would be head + condensation_action
        head = state.history[:min(self.keep_first, len(state.history))] if hasattr(self, 'keep_first') else []
        condensation = head + [condensation_action]
        
        return condensation, last_processed_index
