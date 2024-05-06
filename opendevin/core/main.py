import asyncio
import sys
from typing import Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.core.config import args
from opendevin.core.schema import AgentState
from opendevin.events.action import ChangeAgentStateAction, MessageAction
from opendevin.events.event import Event
from opendevin.events.observation import AgentStateChangedObservation
from opendevin.events.stream import EventSource, EventStream, EventStreamSubscriber
from opendevin.llm.llm import LLM


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def main(task_str: str = ''):
    """Main coroutine to run the agent controller with task input flexibility."""

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

    print(
        f'Running agent {args.agent_cls} (model: {args.model_name}) with task: "{task}"'
    )
    llm = LLM(args.model_name)
    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)
    event_stream = EventStream()
    controller = AgentController(
        agent=agent,
        max_iterations=args.max_iterations,
        max_chars=args.max_chars,
        event_stream=event_stream,
    )

    await controller.setup_task(task)
    await event_stream.add_event(
        ChangeAgentStateAction(agent_state=AgentState.RUNNING), EventSource.USER
    )

    async def on_event(event: Event):
        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state == AgentState.AWAITING_USER_INPUT:
                message = input('Request user input >> ')
                action = MessageAction(content=message)
                await event_stream.add_event(action, EventSource.USER)

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event)
    while controller.get_agent_state() not in [
        AgentState.FINISHED,
        AgentState.ERROR,
        AgentState.STOPPED,
    ]:
        await asyncio.sleep(1)  # Give back control for a tick, so the agent can run


if __name__ == '__main__':
    asyncio.run(main())
