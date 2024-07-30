import base64
import pickle
from dataclasses import dataclass, field
from enum import Enum

from opendevin.controller.state.task import RootTask
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.metrics import Metrics
from opendevin.core.schema import AgentState
from opendevin.events.action import (
    MessageAction,
)
from opendevin.events.action.agent import AgentFinishAction
from opendevin.memory.history import ShortTermHistory
from opendevin.storage.files import FileStore


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
    OpenDevin is a multi-agentic system.

    A `task` is an end-to-end conversation between OpenDevin (the whole sytem) and the
    user, which might involve one or more inputs from the user. It starts with
    an initial input (typically a task statement) from the user, and ends with either
    a `AgentFinishAction` initiated by the agent, or an error.

    A `subtask` is an end-to-end conversation between an agent and the user, or
    another agent. If a `task` is conducted by a single agent, then it's also a `subtask`
    itself. Otherwise, a `task` consists of multiple `subtasks`, each executed by
    one agent.

    A `State` is a mutable object associated with a `subtask`. It includes several
    mutable and immutable fields, among which `iteration` is shared across
    subtasks.

    For example, considering a task from the user: `tell me how many GitHub stars
    OpenDevin repo has`. Let's assume the default agent is CodeActAgent.

    -- TASK STARTS (SUBTASK 0 STARTS) --

    DELEGATE_LEVEL 0, ITERATION 0, LOCAL_ITERATION 0
    CodeActAgent: I should request help from BrowsingAgent

    -- DELEGATE STARTS (SUBTASK 1 STARTS) --

    DELEGATE_LEVEL 1, ITERATION 1, LOCAL_ITERATION 0
    BrowsingAgent: Let me find the answer on GitHub

    DELEGATE_LEVEL 1, ITERATION 2, LOCAL_ITERATION 1
    BrowsingAgent: I found the answer, let me convey the result and finish

    -- DELEGATE ENDS (SUBTASK 1 ENDS) --

    DELEGATE_LEVEL 0, ITERATION 3, LOCAL_ITERATION 1
    CodeActAgent: I got the answer from BrowsingAgent, let me convey the result
    and finish

    -- TASK ENDS (SUBTASK 0 ENDS) --

    Note how ITERATION counter is shared across agents, while LOCAL_ITERATION
    is local to each subtask.
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
        """Returns the latest user message that appears after a FinishAction, or the first (the task) if nothing was finished yet."""
        last_user_message = None
        for event in self.history.get_events(reverse=True):
            if isinstance(event, MessageAction) and event.source == 'user':
                last_user_message = event.content
            elif isinstance(event, AgentFinishAction):
                if last_user_message is not None:
                    return last_user_message

        return last_user_message
