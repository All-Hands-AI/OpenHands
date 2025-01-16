import asyncio
import json
import os
import sys
from typing import Callable, Protocol

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import (
    AppConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.loop import run_agent_until_done
from openhands.core.schema import AgentState
from openhands.core.setup import (
    create_agent,
    create_controller,
    create_runtime,
    generate_sid,
)
from openhands.events import EventSource, EventStreamSubscriber
from openhands.events.action import MessageAction
from openhands.events.action.action import Action
from openhands.events.event import Event
from openhands.events.observation import AgentStateChangedObservation
from openhands.events.serialization.event import event_to_trajectory
from openhands.runtime.base import Runtime


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


def read_input(config: AppConfig) -> str:
    """Read input from user based on config settings."""
    if config.cli_multiline_input:
        print('Enter your message (enter "/exit" on a new line to finish):')
        lines = []
        while True:
            line = input('>> ').rstrip()
            if line == '/exit':  # finish input
                break
            lines.append(line)
        return '\n'.join(lines)
    else:
        return input('>> ').rstrip()


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
    sid = sid or generate_sid(config)

    if runtime is None:
        runtime = create_runtime(config, sid=sid, headless_mode=headless_mode)
        await runtime.connect()

    event_stream = runtime.event_stream

    if agent is None:
        agent = create_agent(runtime, config)

    controller, initial_state = create_controller(agent, runtime, config)

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

    def on_event(event: Event):
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.AWAITING_USER_INPUT:
                if exit_on_message:
                    message = '/exit'
                elif fake_user_response_fn is None:
                    message = read_input(config)
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
    if config.save_trajectory_path is not None:
        # if save_trajectory_path is a folder, use session id as file name
        if os.path.isdir(config.save_trajectory_path):
            file_path = os.path.join(config.save_trajectory_path, sid + '.json')
        else:
            file_path = config.save_trajectory_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        histories = [event_to_trajectory(event) for event in state.history]
        with open(file_path, 'w') as f:
            json.dump(histories, f)

    return state


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

    config = setup_config_from_args(args)

    # Set session name
    session_name = args.name
    sid = generate_sid(config, session_name)

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
