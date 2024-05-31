import asyncio
import sys
from typing import Callable, Optional, Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import args, get_llm_config_arg
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.llm.llm import LLM
from opendevin.runtime.sandbox import Sandbox
from opendevin.runtime.server.runtime import ServerRuntime


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def main(
    task_str: str = '',
    exit_on_message: bool = False,
    fake_user_response_fn: Optional[Callable[[Optional[State]], str]] = None,
    sandbox: Optional[Sandbox] = None,
) -> Optional[State]:
    """Main coroutine to run the agent controller with task input flexibility.
    It's only used when you launch opendevin backend directly via cmdline.

    Args:
        task_str: The task to run.
        exit_on_message: quit if agent asks for a message from user (optional)
        fake_user_response_fn: An optional function that receives the current state (could be None) and returns a fake user response.
        sandbox: An optional sandbox to run the agent in.
    """

    # Determine the task source
    if task_str:
        task = task_str
    elif args.file:
        task = read_task_from_file(args.file)
    elif args.task:
        task = args.task
    elif not sys.stdin.isatty():
        task = read_task_from_stdin()
    else:
        raise ValueError('No task provided. Please specify a task through -t, -f.')

    # only one of model_name or llm_config is required
    if args.llm_config:
        # --llm_config
        # llm_config can contain any of the attributes of LLMConfig
        llm_config = get_llm_config_arg(args.llm_config)

        if llm_config is None:
            raise ValueError(f'Invalid toml file, cannot read {args.llm_config}')

        logger.info(
            f'Running agent {args.agent_cls} (model: {llm_config.model}, llm_config: {args.llm_config}) with task: "{task}"'
        )

        # create LLM instance with the given config
        llm = LLM(llm_config=llm_config)
    else:
        # --model-name model_name
        logger.info(
            f'Running agent {args.agent_cls} (model: {args.model_name}), with task: "{task}"'
        )
        llm = LLM(args.model_name)

    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)

    event_stream = EventStream('main')
    controller = AgentController(
        agent=agent,
        max_iterations=args.max_iterations,
        max_budget_per_task=args.max_budget_per_task,
        max_chars=args.max_chars,
        event_stream=event_stream,
    )
    runtime = ServerRuntime(event_stream=event_stream, sandbox=sandbox)
    runtime.init_sandbox_plugins(controller.agent.sandbox_plugins)

    await event_stream.add_event(MessageAction(content=task), EventSource.USER)

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
                await event_stream.add_event(action, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)
    while controller.get_agent_state() not in [
        AgentState.FINISHED,
        AgentState.ERROR,
        AgentState.PAUSED,
        AgentState.STOPPED,
    ]:
        await asyncio.sleep(1)  # Give back control for a tick, so the agent can run

    await controller.close()
    runtime.close()
    return controller.get_state()


if __name__ == '__main__':
    asyncio.run(main())
