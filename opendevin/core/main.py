import asyncio
import sys
from typing import Optional, Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin.controller import AgentController
from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import args
from opendevin.llm.llm import LLM


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


async def main(task_str: str = '', controller_kwargs: dict = {}) -> Optional[State]:
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
    controller = AgentController(
        agent=agent,
        max_iterations=args.max_iterations,
        max_chars=args.max_chars,
        **(controller_kwargs or {}),
    )

    return await controller.start(task)


if __name__ == '__main__':
    asyncio.run(main())
