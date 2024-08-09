import asyncio
import sys
import uuid
from typing import Callable, Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import (
    AppConfig,
    get_llm_config_arg,
    load_app_config,
    parse_arguments,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.llm.llm import LLM
from opendevin.runtime import get_runtime_cls
from opendevin.runtime.runtime import Runtime
from opendevin.storage import get_file_store


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def create_runtime(
    config: AppConfig,
    sid: str | None = None,
    runtime_tools_config: dict | None = None,
) -> Runtime:
    """Create a runtime for the agent to run on.

    config: The app config.
    sid: The session id.
    runtime_tools_config: (will be deprecated) The runtime tools config.
    """
    # set up the event stream
    file_store = get_file_store(config.file_store, config.file_store_path)
    session_id = 'main' + ('_' + sid if sid else str(uuid.uuid4()))
    event_stream = EventStream(session_id, file_store)

    # agent class
    agent_cls = agenthub.Agent.get_cls(config.default_agent)

    # runtime and tools
    runtime_cls = get_runtime_cls(config.runtime)
    logger.info(f'Initializing runtime: {runtime_cls}')
    runtime: Runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=session_id,
        plugins=agent_cls.sandbox_plugins,
    )
    await runtime.ainit()

    return runtime


async def run_controller(
    config: AppConfig,
    task_str: str,
    runtime: Runtime | None = None,
    agent: Agent | None = None,
    exit_on_message: bool = False,
    fake_user_response_fn: Callable[[State | None], str] | None = None,
    headless_mode: bool = True,
) -> State | None:
    """Main coroutine to run the agent controller with task input flexibility.
    It's only used when you launch opendevin backend directly via cmdline.

    Args:
        config: The app config.
        task_str: The task to run. It can be a string.
        runtime: (optional) A runtime for the agent to run on.
        agent: (optional) A agent to run.
        exit_on_message: quit if agent asks for a message from user (optional)
        fake_user_response_fn: An optional function that receives the current state (could be None) and returns a fake user response.
        headless_mode: Whether the agent is run in headless mode.
    """
    # Create the agent
    if agent is None:
        agent_cls: Type[Agent] = Agent.get_cls(config.default_agent)
        agent = agent_cls(
            llm=LLM(config=config.get_llm_config_from_agent(config.default_agent))
        )

    if runtime is None:
        runtime = await create_runtime(config)

    event_stream = runtime.event_stream
    # restore cli session if enabled
    initial_state = None
    if config.enable_cli_session:
        try:
            logger.info('Restoring agent state from cli session')
            initial_state = State.restore_from_session(
                event_stream.sid, event_stream.file_store
            )
        except Exception as e:
            logger.info('Error restoring state', e)

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

    assert isinstance(task_str, str), f'task_str must be a string, got {type(task_str)}'
    # Logging
    logger.info(
        f'Agent Controller Initialized: Running agent {agent.name}, model {agent.llm.config.model}, with task: "{task_str}"'
    )

    # start event is a MessageAction with the task, either resumed or new
    if config.enable_cli_session and initial_state is not None:
        # we're resuming the previous session
        event_stream.add_event(
            MessageAction(
                content="Let's get back on track. If you experienced errors before, do NOT resume your task. Ask me about it."
            ),
            EventSource.USER,
        )
    elif initial_state is None:
        # init with the provided task
        event_stream.add_event(MessageAction(content=task_str), EventSource.USER)

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
        await asyncio.sleep(1)  # Give back control for a tick, so the agent can run

    # save session when we're about to close
    if config.enable_cli_session:
        end_state = controller.get_state()
        end_state.save_to_session(event_stream.sid, event_stream.file_store)

    # close when done
    await controller.close()
    state = controller.get_state()

    return state


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

    # Load the app config
    # this will load config from config.toml in the current directory
    # as well as from the environment variables
    config = load_app_config()

    # Override default LLM configs ([llm] section in config.toml)
    if args.llm_config:
        llm_config = get_llm_config_arg(args.llm_config)
        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')
        config.set_llm_config(llm_config)

    # Set default agent
    config.default_agent = args.agent_cls

    # if max budget per task is not sent on the command line, use the config value
    if args.max_budget_per_task is not None:
        config.max_budget_per_task = args.max_budget_per_task
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations

    asyncio.run(
        run_controller(
            config=config,
            task_str=task_str,
        )
    )
