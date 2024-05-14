import asyncio
import sys
from typing import Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.core.config import args, get_llm_config_arg
from opendevin.core.schema import AgentState
from opendevin.events.action import ChangeAgentStateAction, MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.events.stream import EventSource, EventStream, EventStreamSubscriber
from opendevin.llm.llm import LLM
from opendevin.runtime.server.runtime import ServerRuntime


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def main(task_str: str = '', exit_on_message: bool = False) -> AgentState:
    """
    Main coroutine to run the agent controller with task input flexibility.
    It's only used when you launch opendevin backend directly via cmdline.

    Args:
        task_str: task string (optional)
        exit_on_message: quit if agent asks for a message from user (optional)

    Returns:
        The final agent state right before shutdown
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

        print(
            f'Running agent {args.agent_cls} (model: {llm_config.model}, llm_config: {llm_config}) with task: "{task}"'
        )

        # create LLM instance with the given config
        llm = LLM(llm_config=llm_config)
    else:
        # --model-name model_name
        print(
            f'Running agent {args.agent_cls} (model: {args.model_name}), with task: "{task}"'
        )
        llm = LLM(args.model_name)

    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)

    event_stream = EventStream('main')
    controller = AgentController(
        agent=agent,
        max_iterations=args.max_iterations,
        max_chars=args.max_chars,
        event_stream=event_stream,
    )
    _ = ServerRuntime(event_stream=event_stream)

    await event_stream.add_event(MessageAction(content=task), EventSource.USER)
    await event_stream.add_event(
        ChangeAgentStateAction(agent_state=AgentState.RUNNING), EventSource.USER
    )

    async def on_event(event: Event):
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.AWAITING_USER_INPUT:
                action = MessageAction(content='/exit')
                if not exit_on_message:
                    message = input('Request user input >> ')
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

    # retrieve the final state before we close the controller and agent
    final_agent_state = controller.get_agent_state()
    await controller.close()
    return final_agent_state


if __name__ == '__main__':
    asyncio.run(main())
