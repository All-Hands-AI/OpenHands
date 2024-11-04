import asyncio
import hashlib
import json
import os
import sys
import uuid
from functools import wraps
from typing import Callable, Protocol, Type, TypeVar, Any

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    get_llm_config_arg,
    load_app_config,
    parse_arguments,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import MessageAction
from openhands.events.action.action import Action
from openhands.events.event import Event
from openhands.events.observation import AgentStateChangedObservation
from openhands.events.serialization.event import event_to_trajectory
from openhands.llm.llm import LLM
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


T = TypeVar('T')


def state_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for state operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.debug(f'Error during {operation_name}: {e}')
            return None
        return wrapper
    return decorator


class FakeUserResponseFunc(Protocol):
    def __call__(
        self,
        state: State,
        encapsulate_solution: bool = ...,
        try_parse: Callable[[Action], str] = ...,
    ) -> str: ...


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


def create_runtime(
    config: AppConfig,
    sid: str | None = None,
) -> Runtime:
    """Create a runtime for the agent to run on."""
    session_id = sid or generate_sid(config)
    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(session_id, file_store)
    agent_cls = openhands.agenthub.Agent.get_cls(config.default_agent)
    runtime_cls = get_runtime_cls(config.runtime)
    logger.debug(f'Initializing runtime: {runtime_cls.__name__}')
    runtime: Runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=session_id,
        plugins=agent_cls.sandbox_plugins,
    )
    return runtime


@state_operation("state_restore")
def restore_initial_state(event_stream: EventStream) -> State | None:
    """Restore state from session"""
    logger.debug(f'Restoring agent state from cli session {event_stream.sid}')
    return State.restore_from_session(event_stream.sid, event_stream.file_store)


async def run_controller(
    config: AppConfig,
    initial_user_action: Action,
    sid: str | None = None,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    exit_on_message: bool = False,
    fake_user_response_fn: FakeUserResponseFunc | None = None,
    headless_mode: bool = True,
) -> State | None:
    """Main coroutine to run the agent controller with task input flexibility."""
    if agent is None:
        agent_cls: Type[Agent] = Agent.get_cls(config.default_agent)
        agent_config = config.get_agent_config(config.default_agent)
        llm_config = config.get_llm_config_from_agent(config.default_agent)
        agent = agent_cls(
            llm=LLM(config=llm_config),
            config=agent_config,
        )

    sid = sid or generate_sid(config)

    if runtime is None:
        runtime = create_runtime(config, sid=sid)
        await runtime.connect()

    event_stream = runtime.event_stream
    initial_state = None
    if config.enable_cli_session:
        initial_state = restore_initial_state(event_stream)

    controller = AgentController(
        agent=agent,
        max_iterations=config.max_iterations,
        max_budget_per_task=config.max_budget_per_task,
        agent_to_llm_config=config.get_agent_to_llm_config_map(),
        event_stream=event_stream,
        initial_state=initial_state,
        headless_mode=headless_mode,
    )

    if controller is not None:
        controller.agent_task = asyncio.create_task(controller.start_step_loop())

    assert isinstance(
        initial_user_action, Action
    ), f'initial user actions must be an Action, got {type(initial_user_action)}'

    logger.debug(
        f'Agent Controller Initialized: Running agent {agent.name}, model '
        f'{agent.llm.config.model}, with actions: {initial_user_action}'
    )

    if config.enable_cli_session and initial_state is not None:
        event_stream.add_event(
            MessageAction(
                content=(
                    "Let's get back on track. If you experienced errors before, do "
                    'NOT resume your task. Ask me about it.'
                ),
            ),
            EventSource.USER,
        )
    elif initial_state is None:
        event_stream.add_event(initial_user_action, EventSource.USER)

    async def on_event(event: Event):
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.AWAITING_USER_INPUT:
                if exit_on_message:
                    message = '/exit'
                elif fake_user_response_fn is None:
                    message = input('Request user input >> ')
                else:
                    message = fake_user_response_fn(controller.get_state())
                action = MessageAction(content=message)
                event_stream.add_event(action, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)
    while controller.state.agent_state not in [
        AgentState.FINISHED,
        AgentState.REJECTED,
        AgentState.ERROR,
        AgentState.PAUSED,
        AgentState.STOPPED,
    ]:
        await asyncio.sleep(1)

    if config.enable_cli_session:
        end_state = controller.get_state()
        end_state.save_to_session(event_stream.sid, event_stream.file_store)

    await controller.close()
    state = controller.get_state()

    if config.trajectories_path is not None:
        save_trajectory(config.trajectories_path, sid, state)

    return state


@state_operation("save_trajectory")
def save_trajectory(trajectories_path: str, sid: str, state: State) -> None:
    """Save trajectory to file"""
    file_path = os.path.join(trajectories_path, sid + '.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    histories = [
        event_to_trajectory(event)
        for event in state.history.get_events(include_delegates=True)
    ]
    with open(file_path, 'w') as f:
        json.dump(histories, f)


def generate_sid(config: AppConfig, session_name: str | None = None) -> str:
    """Generate a session id based on the session name and the jwt secret."""
    session_name = session_name or str(uuid.uuid4())
    jwt_secret = config.jwt_secret
    hash_str = hashlib.sha256(f'{session_name}{jwt_secret}'.encode('utf-8')).hexdigest()
    return f'{session_name}-{hash_str[:16]}'


if __name__ == '__main__':
    args = parse_arguments()

    if args.file:
        task_str = read_task_from_file(args.file)
    elif args.task:
        task_str = args.task
    elif not sys.stdin.isatty():
        task_str = read_task_from_stdin()
    else:
        raise ValueError('No task provided. Please specify a task through -t, -f.')

    initial_user_action: MessageAction = MessageAction(content=task_str)
    config = load_app_config(config_file=args.config_file)

    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')
        config.set_llm_config(llm_config)

    config.default_agent = args.agent_cls
    session_name = args.name
    sid = generate_sid(config, session_name)

    if args.max_budget_per_task is not None:
        config.max_budget_per_task = args.max_budget_per_task
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations

    asyncio.run(
        run_controller(
            config=config,
            initial_user_action=initial_user_action,
            sid=sid,
        )
    )

