import asyncio
import hashlib
import json
import os
import sys
import uuid
from typing import Callable, Protocol, Type

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
from openhands.core.loop import run_agent_until_done
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


class FakeUserResponseFunc(Protocol):
    def __call__(
        self,
        state: State,
        encapsulate_solution: bool = False,
        try_parse: Callable[[Action | None], str] | None = None,
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
    headless_mode: bool = True,
) -> Runtime:
    """Create a runtime for the agent to run on.

    config: The app config.
    sid: (optional) The session id. IMPORTANT: please don't set this unless you know what you're doing.
        Set it to incompatible value will cause unexpected behavior on RemoteRuntime.
    headless_mode: Whether the agent is run in headless mode. `create_runtime` is typically called within evaluation scripts,
        where we don't want to have the VSCode UI open, so it defaults to True.
    """
    # if sid is provided on the command line, use it as the name of the event stream
    # otherwise generate it on the basis of the configured jwt_secret
    # we can do this better, this is just so that the sid is retrieved when we want to restore the session
    session_id = sid or generate_sid(config)

    # set up the event stream
    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(session_id, file_store)

    # agent class
    agent_cls = openhands.agenthub.Agent.get_cls(config.default_agent)

    # runtime and tools
    runtime_cls = get_runtime_cls(config.runtime)
    logger.debug(f'Initializing runtime: {runtime_cls.__name__}')
    runtime: Runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=session_id,
        plugins=agent_cls.sandbox_plugins,
        headless_mode=headless_mode,
    )

    return runtime


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
    """Main coroutine to run the agent controller with task input flexibility.
    It's only used when you launch openhands backend directly via cmdline.

    Args:
        config: The app config.
        initial_user_action: An Action object containing initial user input
        sid: (optional) The session id. IMPORTANT: please don't set this unless you know what you're doing.
            Set it to incompatible value will cause unexpected behavior on RemoteRuntime.
        runtime: (optional) A runtime for the agent to run on.
        agent: (optional) A agent to run.
        exit_on_message: quit if agent asks for a message from user (optional)
        fake_user_response_fn: An optional function that receives the current state
            (could be None) and returns a fake user response.
        headless_mode: Whether the agent is run in headless mode.
    """
    # Create the agent
    if agent is None:
        agent_cls: Type[Agent] = Agent.get_cls(config.default_agent)
        agent_config = config.get_agent_config(config.default_agent)
        llm_config = config.get_llm_config_from_agent(config.default_agent)
        agent = agent_cls(
            llm=LLM(config=llm_config),
            config=agent_config,
        )

    # make sure the session id is set
    sid = sid or generate_sid(config)

    if runtime is None:
        runtime = create_runtime(config, sid=sid, headless_mode=headless_mode)
        await runtime.connect()

    event_stream = runtime.event_stream

    # restore cli session if available
    initial_state = None
    try:
        logger.debug(
            f'Trying to restore agent state from cli session {event_stream.sid} if available'
        )
        initial_state = State.restore_from_session(
            event_stream.sid, event_stream.file_store
        )
    except Exception as e:
        logger.debug(f'Cannot restore agent state: {e}')

    # init controller with this initial state
    controller = AgentController(
        agent=agent,
        max_iterations=config.max_iterations,
        max_budget_per_task=config.max_budget_per_task,
        agent_to_llm_config=config.get_agent_to_llm_config_map(),
        event_stream=event_stream,
        initial_state=initial_state,
        headless_mode=headless_mode,
    )

    assert isinstance(
        initial_user_action, Action
    ), f'initial user actions must be an Action, got {type(initial_user_action)}'
    # Logging
    logger.debug(
        f'Agent Controller Initialized: Running agent {agent.name}, model '
        f'{agent.llm.config.model}, with actions: {initial_user_action}'
    )

    # start event is a MessageAction with the task, either resumed or new
    if initial_state is not None:
        # we're resuming the previous session
        event_stream.add_event(
            MessageAction(
                content=(
                    "Let's get back on track. If you experienced errors before, do "
                    'NOT resume your task. Ask me about it.'
                ),
            ),
            EventSource.USER,
        )
    else:
        # init with the provided actions
        event_stream.add_event(initial_user_action, EventSource.USER)

    async def on_event(event: Event):
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.AWAITING_USER_INPUT:
                if exit_on_message:
                    message = '/exit'
                elif fake_user_response_fn is None:
                    # read until EOF (Ctrl+D on Unix, Ctrl+Z on Windows)
                    print('Request user input (press Ctrl+D/Z when done) >> ')
                    message = sys.stdin.read().rstrip()
                else:
                    message = fake_user_response_fn(controller.get_state())
                action = MessageAction(content=message)
                event_stream.add_event(action, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event, sid)

    end_states = [
        AgentState.FINISHED,
        AgentState.REJECTED,
        AgentState.ERROR,
        AgentState.PAUSED,
        AgentState.STOPPED,
    ]

    try:
        await run_agent_until_done(controller, runtime, end_states)
    except Exception as e:
        logger.error(f'Exception in main loop: {e}')

    # save session when we're about to close
    if config.file_store is not None and config.file_store != 'memory':
        end_state = controller.get_state()
        # NOTE: the saved state does not include delegates events
        end_state.save_to_session(event_stream.sid, event_stream.file_store)

    state = controller.get_state()

    # save trajectories if applicable
    if config.trajectories_path is not None:
        # if trajectories_path is a folder, use session id as file name
        if os.path.isdir(config.trajectories_path):
            file_path = os.path.join(config.trajectories_path, sid + '.json')
        else:
            file_path = config.trajectories_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        histories = [event_to_trajectory(event) for event in state.history]
        with open(file_path, 'w') as f:
            json.dump(histories, f)

    return state


def generate_sid(config: AppConfig, session_name: str | None = None) -> str:
    """Generate a session id based on the session name and the jwt secret."""
    session_name = session_name or str(uuid.uuid4())
    jwt_secret = config.jwt_secret

    hash_str = hashlib.sha256(f'{session_name}{jwt_secret}'.encode('utf-8')).hexdigest()
    return f'{session_name}-{hash_str[:16]}'


def auto_continue_response(
    state: State,
    encapsulate_solution: bool = False,
    try_parse: Callable[[Action | None], str] | None = None,
) -> str:
    """Default function to generate user responses.
    Tell the agent to proceed without asking for more input, or finish the interaction.
    """
    message = (
        'Please continue on whatever approach you think is suitable.\n'
        'If you think you have solved the task, please finish the interaction.\n'
        'IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN RESPONSE.\n'
    )
    return message


if __name__ == '__main__':
    args = parse_arguments()

    # Determine the task
    if args.file:
        task_str = read_task_from_file(args.file)
    elif args.task:
        task_str = args.task
    elif not sys.stdin.isatty():
        task_str = read_task_from_stdin()
    else:
        raise ValueError('No task provided. Please specify a task through -t, -f.')
    initial_user_action: MessageAction = MessageAction(content=task_str)
    # Load the app config
    # this will load config from config.toml in the current directory
    # as well as from the environment variables
    config = load_app_config(config_file=args.config_file)

    # Override default LLM configs ([llm] section in config.toml)
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')
        config.set_llm_config(llm_config)

    # Set default agent
    config.default_agent = args.agent_cls

    # Set session name
    session_name = args.name
    sid = generate_sid(config, session_name)

    # if max budget per task is not sent on the command line, use the config value
    if args.max_budget_per_task is not None:
        config.max_budget_per_task = args.max_budget_per_task
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations

    asyncio.run(
        run_controller(
            config=config,
            initial_user_action=initial_user_action,
            sid=sid,
            fake_user_response_fn=None
            if args.no_auto_continue
            else auto_continue_response,
        )
    )
