from __future__ import annotations

import base64
import os
import pickle
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import openhands
from openhands.controller.state.task import RootTask
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.events.action import (
    MessageAction,
)
from openhands.events.action.agent import AgentFinishAction
from openhands.events.event import Event, EventSource
from openhands.llm.metrics import Metrics
from openhands.memory.view import View
from openhands.storage.files import FileStore
from openhands.storage.locations import get_conversation_agent_state_filename


class TrafficControlState(str, Enum):
    # default state, no rate limiting
    NORMAL = 'normal'

    # task paused due to traffic control
    THROTTLING = 'throttling'

    # traffic control is temporarily paused
    PAUSED = 'paused'


RESUMABLE_STATES = [
    AgentState.RUNNING,
    AgentState.PAUSED,
    AgentState.AWAITING_USER_INPUT,
    AgentState.FINISHED,
]


@dataclass
class State:
    """
    Represents the running state of an agent in the OpenHands system, saving data of its operation and memory.

    - Multi-agent/delegate state:
      - store the task (conversation between the agent and the user)
      - the subtask (conversation between an agent and the user or another agent)
      - global and local iterations
      - delegate levels for multi-agent interactions
      - almost stuck state

    - Running state of an agent:
      - current agent state (e.g., LOADING, RUNNING, PAUSED)
      - traffic control state for rate limiting
      - confirmation mode
      - the last error encountered

    - Data for saving and restoring the agent:
      - save to and restore from a session
      - serialize with pickle and base64

    - Save / restore data about message history
      - start and end IDs for events in agent's history
      - summaries and delegate summaries

    - Metrics:
      - global metrics for the current task
      - local metrics for the current subtask

    - Extra data:
      - additional task-specific data
    """

    root_task: RootTask = field(default_factory=RootTask)
    session_id: str = ''
    # global iteration for the current task
    iteration: int = 0
    # local iteration for the current subtask
    local_iteration: int = 0
    # max number of iterations for the current task
    max_iterations: int = 100
    confirmation_mode: bool = False
    history: list[Event] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    agent_state: AgentState = AgentState.LOADING
    resume_state: AgentState | None = None
    traffic_control_state: TrafficControlState = TrafficControlState.NORMAL
    # global metrics for the current task
    metrics: Metrics = field(default_factory=Metrics)
    # local metrics for the current subtask
    local_metrics: Metrics = field(default_factory=Metrics)
    # root agent has level 0, and every delegate increases the level by one
    delegate_level: int = 0
    # start_id and end_id track the range of events in history
    start_id: int = -1
    end_id: int = -1

    delegates: dict[tuple[int, int], tuple[str, str]] = field(default_factory=dict)
    # NOTE: This will never be used by the controller, but it can be used by different
    # evaluation tasks to store extra data needed to track the progress/state of the task.
    extra_data: dict[str, Any] = field(default_factory=dict)
    last_error: str = ''

    def save_to_session(
        self, sid: str, file_store: FileStore, user_id: str | None
    ) -> None:
        pickled = pickle.dumps(self)
        logger.debug(f'Saving state to session {sid}:{self.agent_state}')
        encoded = base64.b64encode(pickled).decode('utf-8')
        try:
            file_store.write(
                get_conversation_agent_state_filename(sid, user_id), encoded
            )

            # see if state is in the old directory on saas/remote use cases and delete it.
            if user_id:
                filename = get_conversation_agent_state_filename(sid)
                try:
                    file_store.delete(filename)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f'Failed to save state to session: {e}')
            raise e

    @staticmethod
    def restore_from_session(
        sid: str, file_store: FileStore, user_id: str | None = None
    ) -> 'State':
        """
        Restores the state from the previously saved session.
        """

        state: State
        try:
            encoded = file_store.read(
                get_conversation_agent_state_filename(sid, user_id)
            )
            pickled = base64.b64decode(encoded)
            state = pickle.loads(pickled)
        except FileNotFoundError:
            # if user_id is provided, we are in a saas/remote use case
            # and we need to check if the state is in the old directory.
            if user_id:
                filename = get_conversation_agent_state_filename(sid)
                encoded = file_store.read(filename)
                pickled = base64.b64decode(encoded)
                state = pickle.loads(pickled)
            else:
                raise FileNotFoundError(
                    f'Could not restore state from session file for sid: {sid}'
                )
        except Exception as e:
            logger.debug(f'Could not restore state from session: {e}')
            raise e

        # update state
        if state.agent_state in RESUMABLE_STATES:
            state.resume_state = state.agent_state
        else:
            state.resume_state = None

        # first state after restore
        state.agent_state = AgentState.LOADING
        return state

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

    def get_current_user_intent(self) -> tuple[str | None, list[str] | None]:
        """Returns the latest user message and image(if provided) that appears after a FinishAction, or the first (the task) if nothing was finished yet."""
        last_user_message = None
        last_user_message_image_urls: list[str] | None = []
        for event in reversed(self.view):
            if isinstance(event, MessageAction) and event.source == 'user':
                last_user_message = event.content
                last_user_message_image_urls = event.image_urls
            elif isinstance(event, AgentFinishAction):
                if last_user_message is not None:
                    return last_user_message, None

        return last_user_message, last_user_message_image_urls

    def get_last_agent_message(self) -> MessageAction | None:
        for event in reversed(self.view):
            if isinstance(event, MessageAction) and event.source == EventSource.AGENT:
                return event
        return None

    def get_last_user_message(self) -> MessageAction | None:
        for event in reversed(self.view):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return event
        return None

    def to_llm_metadata(self, agent_name: str) -> dict:
        return {
            'session_id': self.session_id,
            'trace_version': openhands.__version__,
            'tags': [
                f'agent:{agent_name}',
                f"web_host:{os.environ.get('WEB_HOST', 'unspecified')}",
                f'openhands_version:{openhands.__version__}',
            ],
        }

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
