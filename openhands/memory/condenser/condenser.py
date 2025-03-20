from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, overload

from pydantic import BaseModel

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import CondenserConfig
from openhands.events.action.agent import CondensationAction
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


class View(BaseModel):
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


class Condensation(BaseModel):
    action: CondensationAction


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
    def condense(self, events: list[Event]) -> View | Condensation:
        """Condense a sequence of events into a potentially smaller list.

        New condenser strategies should override this method to implement their own condensation logic. Call `self.add_metadata` in the implementation to record any relevant per-condensation diagnostic information.

        Args:
            events: A list of events representing the entire history of the agent.

        Returns:
            list[Event]: An event sequence representing a condensed history of the agent.
        """

    def condensed_history(self, state: State) -> View | Condensation:
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
    """Base class for a specialized condenser strategy that applies condensation to a rolling history."""

    def __init__(self) -> None:
        self._condensation: list[Event] = []
        self._last_history_length: int = 0

        super().__init__()

    @abstractmethod
    def should_condense(self, view: View) -> bool:
        """Determine if a view should be condensed."""

    @abstractmethod
    def get_view(self, events: list[Event]) -> View:
        """Get the view from a list of events."""

    @abstractmethod
    def get_condensation(self, view: View) -> Condensation:
        """Get the condensation from a view."""

    def condense(self, events: list[Event]) -> View | Condensation:
        # Convert the state to a view. This might require some condenser-specific logic.
        view = self.get_view(events)

        # If we trigger the condenser-specific condensation threshold, compute and return
        # the condensation.
        if self.should_condense(view):
            return self.get_condensation(view)

        # Otherwise we're safe to just return the view.
        else:
            return view
