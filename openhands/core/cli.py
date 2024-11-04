import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Type, TypeVar

from termcolor import colored

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands import __version__
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.core.config import (
    get_parser,
    load_app_config,
)
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream, EventStreamSubscriber
from openhands.events.action import (
    Action,
    ChangeAgentStateAction,
    CmdRunAction,
    FileEditAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    FileEditObservation,
)
from openhands.llm.llm import LLM
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


T = TypeVar('T')


def cli_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for CLI operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f'Error during {operation_name}: {e}')
                print(f'An error occurred during {operation_name}. Please try again.')
            return None
        return wrapper
    return decorator


@cli_operation("display")
def display_message(message: str):
    print(colored('🤖 ' + message + '\n', 'yellow'))


@cli_operation("display")
def display_command(command: str):
    print('❯ ' + colored(command + '\n', 'green'))


@cli_operation("display")
def display_command_output(output: str):
    lines = output.split('\n')
    for line in lines:
        if line.startswith('[Python Interpreter') or line.startswith('openhands@'):
            continue
        print(colored(line, 'blue'))
    print('\n')


@cli_operation("display")
def display_file_edit(event: FileEditAction | FileEditObservation):
    print(colored(str(event), 'green'))


@cli_operation("display")
def display_event(event: Event):
    if isinstance(event, Action):
        if hasattr(event, 'thought'):
            display_message(event.thought)
    if isinstance(event, MessageAction):
        if event.source == EventSource.AGENT:
            display_message(event.content)
    if isinstance(event, CmdRunAction):
        display_command(event.command)
    if isinstance(event, CmdOutputObservation):
        display_command_output(event.content)
    if isinstance(event, FileEditAction):
        display_file_edit(event)
    if isinstance(event, FileEditObservation):
        display_file_edit(event)


async def main():
    """Runs the agent in CLI mode"""
    parser = get_parser()
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=f'{__version__}',
        help='Show the version number and exit',
        default=None,
    )
    args = parser.parse_args()

    if args.version:
        print(f'OpenHands version: {__version__}')
        return

    logger.setLevel(logging.WARNING)
    config = load_app_config(config_file=args.config_file)
    sid = 'cli'

    agent_cls: Type[Agent] = Agent.get_cls(config.default_agent)
    agent_config = config.get_agent_config(config.default_agent)
    llm_config = config.get_llm_config_from_agent(config.default_agent)
    agent = agent_cls(
        llm=LLM(config=llm_config),
        config=agent_config,
    )

    file_store = get_file_store(config.file_store, config.file_store_path)
    event_stream = EventStream(sid, file_store)

    runtime_cls = get_runtime_cls(config.runtime)
    runtime: Runtime = runtime_cls(
        config=config,
        event_stream=event_stream,
        sid=sid,
        plugins=agent_cls.sandbox_plugins,
    )
    await runtime.connect()

    controller = AgentController(
        agent=agent,
        max_iterations=config.max_iterations,
        max_budget_per_task=config.max_budget_per_task,
        agent_to_llm_config=config.get_agent_to_llm_config_map(),
        event_stream=event_stream,
    )

    if controller is not None:
        controller.agent_task = asyncio.create_task(controller.start_step_loop())

    @cli_operation("prompt")
    async def prompt_for_next_task():
        next_message = input('How can I help? >> ')
        if next_message == 'exit':
            event_stream.add_event(
                ChangeAgentStateAction(AgentState.STOPPED), EventSource.ENVIRONMENT
            )
            return
        action = MessageAction(content=next_message)
        event_stream.add_event(action, EventSource.USER)

    async def on_event(event: Event):
        display_event(event)
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.ERROR:
                print('An error occurred. Please try again.')
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
                AgentState.ERROR,
            ]:
                await prompt_for_next_task()

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)
    await prompt_for_next_task()

    while controller.state.agent_state not in [AgentState.STOPPED]:
        await asyncio.sleep(1)

    print('Exiting...')
    await controller.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        pass

