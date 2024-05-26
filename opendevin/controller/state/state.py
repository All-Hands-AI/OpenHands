import base64
import pickle
from dataclasses import dataclass, field

from opendevin.controller.state.task import RootTask
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.metrics import Metrics
from opendevin.core.schema import AgentState
from opendevin.events.action import (
    Action,
    MessageAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    Observation,
)
from opendevin.storage import get_file_store

RESUMABLE_STATES = [
    AgentState.RUNNING,
    AgentState.PAUSED,
    AgentState.AWAITING_USER_INPUT,
    AgentState.FINISHED,
]


@dataclass
class State:
    root_task: RootTask = field(default_factory=RootTask)
    iteration: int = 0
    max_iterations: int = 100
    # number of characters we have sent to and received from LLM so far for current task
    num_of_chars: int = 0
    background_commands_obs: list[CmdOutputObservation] = field(default_factory=list)
    history: list[tuple[Action, Observation]] = field(default_factory=list)
    updated_info: list[tuple[Action, Observation]] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    error: str | None = None
    agent_state: AgentState = AgentState.LOADING
    resume_state: AgentState | None = None
    metrics: Metrics = Metrics()

    def save_to_session(self, sid: str):
        fs = get_file_store()
        pickled = pickle.dumps(self)
        encoded = base64.b64encode(pickled).decode('utf-8')
        try:
            fs.write(f'sessions/{sid}/agent_state.pkl', encoded)
        except Exception as e:
            logger.error(f'Failed to save state to session: {e}')
            raise e

    @staticmethod
    def restore_from_session(sid: str) -> 'State':
        fs = get_file_store()
        try:
            encoded = fs.read(f'sessions/{sid}/agent_state.pkl')
            pickled = base64.b64decode(encoded)
            state = pickle.loads(pickled)
        except Exception as e:
            logger.error(f'Failed to restore state from session: {e}')
            raise e
        if state.agent_state in RESUMABLE_STATES:
            state.resume_state = state.agent_state
        else:
            state.resume_state = None
        state.agent_state = AgentState.LOADING
        return state

    def get_current_user_intent(self):
        # TODO: this is used to understand the user's main goal, but it's possible
        # the latest message is an interruption. We should look for a space where
        # the agent goes to FINISHED, and then look for the next user message.
        for action, obs in reversed(self.history):
            if isinstance(action, MessageAction) and action.source == 'user':
                return action.content
