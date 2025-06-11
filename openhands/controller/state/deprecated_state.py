from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openhands.core.schema import AgentState
from openhands.events.event import Event
from openhands.llm.metrics import Metrics
from openhands.memory.view import View


@dataclass
class DeprecatedState:
    """
    Represents the old version of the State class, before the IterationControlFlag refactoring.
    This class is used for backward compatibility when deserializing old state objects.
    """

    session_id: str = ''
    iteration: int = 0
    max_iterations: int = 100
    confirmation_mode: bool = False
    history: list[Event] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    agent_state: AgentState = AgentState.LOADING
    resume_state: AgentState | None = None
    # global metrics for the current task
    metrics: Metrics = field(default_factory=Metrics)
    # root agent has level 0, and every delegate increases the level by one
    delegate_level: int = 0
    # start_id and end_id track the range of events in history
    start_id: int = -1
    end_id: int = -1

    parent_metrics_snapshot: Metrics | None = None
    parent_iteration: int = 100

    # NOTE: this is used by the controller to track parent's metrics snapshot before delegation
    # evaluation tasks to store extra data needed to track the progress/state of the task.
    extra_data: dict[str, Any] = field(default_factory=dict)
    last_error: str = ''

    def __getstate__(self) -> dict:
        # don't pickle history, it will be restored from the event stream
        state = self.__dict__.copy()
        state['history'] = []

        # Remove any view caching attributes. They'll be rebuilt frmo the
        # history after that gets reloaded.
        state.pop('_history_checksum', None)
        state.pop('_view', None)

        return state

    def __setstate__(self, state: dict) -> None:
        self.__dict__.update(state)

        # make sure we always have the attribute history
        if not hasattr(self, 'history'):
            self.history = []

    @property
    def view(self) -> View:
        # Compute a simple checksum from the history to see if we can re-use any
        # cached view.
        history_checksum = len(self.history)
        old_history_checksum = getattr(self, '_history_checksum', -1)

        # If the history has changed, we need to re-create the view and update
        # the caching.
        if history_checksum != old_history_checksum:
            self._history_checksum = history_checksum
            self._view = View.from_events(self.history)

        return self._view
