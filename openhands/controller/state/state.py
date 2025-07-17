import base64
import json
import os
import pickle
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import openhands
from openhands.controller.state.task import RootTask
from openhands.core.config import load_app_config
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
from openhands.storage.local import LocalFileStore
from openhands.storage.locations import get_conversation_agent_state_filename

_config_app = None


def get_config_app():
    """Lazy loading of app config to prevent JWT secret creation during module import."""
    global _config_app
    if _config_app is None:
        _config_app = load_app_config()
    return _config_app


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
    user_id: str | None = None

    def save_to_session(self, sid: str, file_store: FileStore, user_id: str | None):
        # Check if we're using DatabaseFileStore
        if get_config_app().file_store == 'database':
            # Use JSON format for database storage
            self.save_to_session_json(sid, file_store, user_id)
            if get_config_app().enable_write_to_local:
                local_file_store = LocalFileStore(get_config_app().file_store_path)
                pickled = pickle.dumps(self)
                encoded = base64.b64encode(pickled).decode('utf-8')
                local_file_store.write(
                    get_conversation_agent_state_filename(sid, user_id), encoded
                )

        else:
            # Use original pickle format for other file stores
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
        # Check if we're using DatabaseFileStore
        if get_config_app().file_store == 'database':
            # Use JSON format for database storage
            return State.restore_from_session_json(sid, file_store, user_id)
        else:
            # Use original pickle format for other file stores with backward compatibility
            state: State
            try:
                data = file_store.read(
                    get_conversation_agent_state_filename(sid, user_id)
                )

                # Try JSON first (new format) for backward compatibility
                try:
                    state = State.from_json(data)
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Fall back to pickle format (old format)
                    pickled = base64.b64decode(data)
                    state = pickle.loads(pickled)

            except FileNotFoundError:
                # if user_id is provided, we are in a saas/remote use case
                # and we need to check if the state is in the old directory.
                if user_id:
                    filename = get_conversation_agent_state_filename(sid)
                    data = file_store.read(filename)

                    # Try JSON first (new format)
                    try:
                        state = State.from_json(data)
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # Fall back to pickle format (old format)
                        pickled = base64.b64decode(data)
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
            # logger.info(f'Restored state: {state.to_json()}')
            return state

    @staticmethod
    def restore_from_session_json(
        sid: str, file_store: FileStore, user_id: str | None = None
    ) -> 'State':
        """
        Restores the state from the previously saved session using JSON format.
        """
        state: State
        try:
            json_data = file_store.read(
                get_conversation_agent_state_filename(sid, user_id)
            )
            state = State.from_json(json_data)

        except FileNotFoundError:
            # if user_id is provided, we are in a saas/remote use case
            # and we need to check if the state is in the old directory.
            if user_id:
                filename = get_conversation_agent_state_filename(sid)
                json_data = file_store.read(filename)
                state = State.from_json(json_data)
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

    def __getstate__(self):
        # don't pickle history, it will be restored from the event stream
        state = self.__dict__.copy()
        state['history'] = []

        # Remove any view caching attributes. They'll be rebuilt frmo the
        # history after that gets reloaded.
        state.pop('_history_checksum', None)
        state.pop('_view', None)

        return state

    def __setstate__(self, state):
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

    def to_json(self) -> str:
        """Convert state to JSON format for database storage."""

        def serialize_metrics(metrics):
            """Helper function to safely serialize Metrics objects."""
            if not hasattr(metrics, '__dict__'):
                return {}

            # Use the get() method which properly serializes all complex objects
            try:
                return metrics.get()
            except Exception:
                # Fallback to manual serialization
                metrics_dict = {}
                for key, value in metrics.__dict__.items():
                    try:
                        # Try to serialize the value as JSON to check if it's serializable
                        json.dumps(value)
                        metrics_dict[key] = value
                    except (TypeError, ValueError):
                        # Handle special cases for complex objects
                        if hasattr(value, 'model_dump'):  # Pydantic models
                            metrics_dict[key] = value.model_dump()
                        elif hasattr(value, '__dict__'):
                            # If it's an object with attributes, try to get its dict
                            try:
                                metrics_dict[key] = value.__dict__
                            except Exception:
                                metrics_dict[key] = str(value)
                        else:
                            # Convert to string as fallback
                            metrics_dict[key] = str(value)
                return metrics_dict

        # Manual serialization to handle complex objects properly
        state_dict = {
            'root_task': self.root_task.__dict__
            if hasattr(self.root_task, '__dict__')
            else {},
            'session_id': self.session_id,
            'iteration': self.iteration,
            'local_iteration': self.local_iteration,
            'max_iterations': self.max_iterations,
            'confirmation_mode': self.confirmation_mode,
            # history is excluded - will be restored from event stream
            'inputs': self.inputs,
            'outputs': self.outputs,
            'agent_state': self.agent_state.value
            if isinstance(self.agent_state, AgentState)
            else self.agent_state,
            'resume_state': self.resume_state.value
            if isinstance(self.resume_state, AgentState)
            else self.resume_state,
            'traffic_control_state': self.traffic_control_state.value
            if isinstance(self.traffic_control_state, TrafficControlState)
            else self.traffic_control_state,
            'metrics': serialize_metrics(self.metrics),
            'local_metrics': serialize_metrics(self.local_metrics),
            'delegate_level': self.delegate_level,
            'start_id': self.start_id,
            'end_id': self.end_id,
            'delegates': {
                f'{k[0]},{k[1]}': v for k, v in self.delegates.items()
            },  # Convert tuple keys to strings
            'extra_data': self.extra_data,
            'last_error': self.last_error,
            'user_id': self.user_id,
        }

        return json.dumps(state_dict, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'State':
        """Create State object from JSON string."""
        from openhands.llm.metrics import Cost, Metrics, ResponseLatency, TokenUsage

        data = json.loads(json_str)

        # Create State object with defaults first
        state = cls()

        # Restore simple fields
        state.session_id = data.get('session_id', '')
        state.iteration = data.get('iteration', 0)
        state.local_iteration = data.get('local_iteration', 0)
        state.max_iterations = data.get('max_iterations', 100)
        state.confirmation_mode = data.get('confirmation_mode', False)
        state.inputs = data.get('inputs', {})
        state.outputs = data.get('outputs', {})
        state.delegate_level = data.get('delegate_level', 0)
        state.start_id = data.get('start_id', -1)
        state.end_id = data.get('end_id', -1)
        state.extra_data = data.get('extra_data', {})
        state.last_error = data.get('last_error', '')
        state.user_id = data.get('user_id')

        # Restore enums
        if 'agent_state' in data:
            try:
                state.agent_state = AgentState(data['agent_state'])
            except (ValueError, TypeError):
                state.agent_state = AgentState.LOADING

        if 'resume_state' in data and data['resume_state'] is not None:
            try:
                state.resume_state = AgentState(data['resume_state'])
            except (ValueError, TypeError):
                state.resume_state = None
        else:
            state.resume_state = None

        if 'traffic_control_state' in data:
            try:
                state.traffic_control_state = TrafficControlState(
                    data['traffic_control_state']
                )
            except (ValueError, TypeError):
                state.traffic_control_state = TrafficControlState.NORMAL

        # Restore complex objects
        # Root task
        if 'root_task' in data and isinstance(data['root_task'], dict):
            root_task = RootTask()
            root_task.__dict__.update(data['root_task'])
            state.root_task = root_task

        # Helper function to restore metrics
        def restore_metrics(metrics_data: dict, model_name: str = 'default') -> Metrics:
            """Restore a Metrics object from serialized data."""
            metrics = Metrics(model_name=model_name)
            # Restore accumulated cost
            if 'accumulated_cost' in metrics_data:
                try:
                    metrics.accumulated_cost = float(metrics_data['accumulated_cost'])
                except (ValueError, TypeError):
                    metrics.accumulated_cost = 0.0

            # Restore accumulated token usage
            if 'accumulated_token_usage' in metrics_data:
                token_data = metrics_data['accumulated_token_usage']
                if isinstance(token_data, dict):
                    try:
                        metrics._accumulated_token_usage = TokenUsage(
                            model=token_data.get('model', model_name),
                            prompt_tokens=int(token_data.get('prompt_tokens', 0)),
                            completion_tokens=int(
                                token_data.get('completion_tokens', 0)
                            ),
                            cache_read_tokens=int(
                                token_data.get('cache_read_tokens', 0)
                            ),
                            cache_write_tokens=int(
                                token_data.get('cache_write_tokens', 0)
                            ),
                            response_id=str(token_data.get('response_id', '')),
                        )
                    except Exception:
                        # Use default if restoration fails
                        pass

            # Restore costs
            if 'costs' in metrics_data and isinstance(metrics_data['costs'], list):
                try:
                    for cost_data in metrics_data['costs']:
                        if isinstance(cost_data, dict):
                            cost = Cost(
                                model=cost_data.get('model', model_name),
                                cost=float(cost_data.get('cost', 0.0)),
                                timestamp=float(
                                    cost_data.get('timestamp', time.time())
                                ),
                            )
                            metrics._costs.append(cost)
                except Exception:
                    # Skip costs if restoration fails
                    pass

            # Restore response latencies
            if 'response_latencies' in metrics_data and isinstance(
                metrics_data['response_latencies'], list
            ):
                try:
                    for latency_data in metrics_data['response_latencies']:
                        if isinstance(latency_data, dict):
                            latency = ResponseLatency(
                                model=latency_data.get('model', model_name),
                                latency=float(latency_data.get('latency', 0.0)),
                                response_id=str(latency_data.get('response_id', '')),
                            )
                            metrics._response_latencies.append(latency)
                except Exception:
                    # Skip latencies if restoration fails
                    pass

            # Restore token usages
            if 'token_usages' in metrics_data and isinstance(
                metrics_data['token_usages'], list
            ):
                try:
                    for usage_data in metrics_data['token_usages']:
                        if isinstance(usage_data, dict):
                            usage = TokenUsage(
                                model=usage_data.get('model', model_name),
                                prompt_tokens=int(usage_data.get('prompt_tokens', 0)),
                                completion_tokens=int(
                                    usage_data.get('completion_tokens', 0)
                                ),
                                cache_read_tokens=int(
                                    usage_data.get('cache_read_tokens', 0)
                                ),
                                cache_write_tokens=int(
                                    usage_data.get('cache_write_tokens', 0)
                                ),
                                response_id=str(usage_data.get('response_id', '')),
                            )
                            metrics._token_usages.append(usage)
                except Exception:
                    # Skip usages if restoration fails
                    pass

            return metrics

        # Restore metrics
        if 'metrics' in data and isinstance(data['metrics'], dict):
            state.metrics = restore_metrics(data['metrics'])

        if 'local_metrics' in data and isinstance(data['local_metrics'], dict):
            state.local_metrics = restore_metrics(data['local_metrics'])

        # Delegates - convert string keys back to tuple keys
        if 'delegates' in data and isinstance(data['delegates'], dict):
            delegates = {}
            for k, v in data['delegates'].items():
                try:
                    # Convert "x,y" back to (x, y)
                    parts = k.split(',')
                    if len(parts) == 2:
                        tuple_key = (int(parts[0]), int(parts[1]))
                        delegates[tuple_key] = v
                except (ValueError, IndexError):
                    continue
            state.delegates = delegates

        # History will be empty and restored from event stream
        state.history = []

        return state

    def save_to_session_json(
        self, sid: str, file_store: FileStore, user_id: str | None
    ):
        """Save state to session using JSON format."""
        logger.info(f'Saving state to session {sid}:{self.agent_state}')
        json_data = self.to_json()
        try:
            file_store.write(
                get_conversation_agent_state_filename(sid, user_id), json_data
            )

            # see if state is in the old directory on saas/remote use cases and delete it.
            if (
                get_config_app().file_store != 'database'
                and get_config_app().file_store_path
            ):
                if user_id:
                    filename = get_conversation_agent_state_filename(sid)
                    try:
                        file_store.delete(filename)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f'Failed to save state to session: {e}')
            raise e
