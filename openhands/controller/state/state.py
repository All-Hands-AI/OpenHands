import base64
import pickle
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openhands.controller.state.task import RootTask
from openhands.core.logger import openhands_logger as logger
from openhands.core.metrics import Metrics
from openhands.core.schema import AgentState
from openhands.events.action import (
    MessageAction,
)
from openhands.events.action.agent import AgentFinishAction
from openhands.memory.history import ShortTermHistory
from openhands.storage.files import FileStore


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
    # global iteration for the current task
    iteration: int = 0
    # local iteration for the current subtask
    local_iteration: int = 0
    # max number of iterations for the current task
    max_iterations: int = 100
    confirmation_mode: bool = False
    history: ShortTermHistory = field(default_factory=ShortTermHistory)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    last_error: str | None = None
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
    almost_stuck: int = 0
    # NOTE: This will never be used by the controller, but it can be used by different
    # evaluation tasks to store extra data needed to track the progress/state of the task.
    extra_data: dict[str, Any] = field(default_factory=dict)

    def save_to_session(self, sid: str, file_store: FileStore):
        pickled = pickle.dumps(self)
        logger.debug(f'Saving state to session {sid}:{self.agent_state}')
        encoded = base64.b64encode(pickled).decode('utf-8')
        try:
            file_store.write(f'sessions/{sid}/agent_state.pkl', encoded)
        except Exception as e:
            logger.error(f'Failed to save state to session: {e}')
            raise e

    @staticmethod
    def restore_from_session(sid: str, file_store: FileStore) -> 'State':
        try:
            encoded = file_store.read(f'sessions/{sid}/agent_state.pkl')
            pickled = base64.b64decode(encoded)
            state = pickle.loads(pickled)
        except Exception as e:
            logger.error(f'Failed to restore state from session: {e}')
            raise e

        # update state
        if state.agent_state in RESUMABLE_STATES:
            state.resume_state = state.agent_state
        else:
            state.resume_state = None

        # don't carry last_error anymore after restore
        state.last_error = None

        # first state after restore
        state.agent_state = AgentState.LOADING
        return state

    def __getstate__(self):
        state = self.__dict__.copy()

        # save the relevant data from recent history
        # so that we can restore it when the state is restored
        if 'history' in state:
            state['start_id'] = state['history'].start_id
            state['end_id'] = state['history'].end_id

        # don't save history object itself
        state.pop('history', None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        # recreate the history object
        if not hasattr(self, 'history'):
            self.history = ShortTermHistory()

        # restore the relevant data in history from the state
        self.history.start_id = self.start_id
        self.history.end_id = self.end_id

        # remove the restored data from the state if any

    def get_current_user_intent(self):
        """Returns the latest user message and image(if provided) that appears after a FinishAction, or the first (the task) if nothing was finished yet."""
        last_user_message = None
        last_user_message_image_urls: list[str] | None = []
        for event in self.history.get_events(reverse=True):
            if isinstance(event, MessageAction) and event.source == 'user':
                last_user_message = event.content
                last_user_message_image_urls = event.images_urls
            elif isinstance(event, AgentFinishAction):
                if last_user_message is not None:
                    return last_user_message

        return last_user_message, last_user_message_image_urls
