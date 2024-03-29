import asyncio
import argparse
import sys
from typing import Type

import agenthub  # noqa: F401
from opendevin.agent import Agent
from opendevin.controller import AgentController
from opendevin.llm.llm import LLM

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for running an agent with various task inputs."""
    parser = argparse.ArgumentParser(description="Run an agent with a specific task or a task read from a file/stdin.")
    parser.add_argument("-d", "--directory", required=True, help="The working directory for the agent.")
    parser.add_argument("-t", "--task", help="The task for the agent to perform. This is overridden if --file is provided.")
    parser.add_argument("-f", "--task-file", help="Path to a file containing the task. Overrides --task if provided.")
    parser.add_argument("-c", "--agent-cls", default="LangchainsAgent", help="The agent class to use.")
    parser.add_argument("-m", "--model-name", default="gpt-4-0125-preview", help="The (litellm) model name to use, defaults to env LLM_MODEL or gpt-4-0125-preview.")
    parser.add_argument("-i", "--max-iterations", type=int, default=100, help="The maximum number of iterations to run the agent.")
    return parser.parse_args()

def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read().strip()

async def main():
    """Main coroutine to run the agent controller with flexible task input."""
    args = parse_arguments()

    task = args.task
    if args.file:
        task = read_task_from_file(args.file)
    elif not sys.stdin.isatty():
        task = read_task_from_stdin()

    if not task:
        raise ValueError("No task provided. Please specify a task through -t, -f.")

    print(f"Running agent {args.agent_cls} with model: {args.model_name}, directory: {args.directory}, task: \"{task}\"")

    llm = LLM(model_name=args.model_name)
    AgentCls: Type[Agent] = getattr(Agent, f"get_{args.agent_cls}_cls", None)
    if not AgentCls:
        raise ValueError(f"Agent class '{args.agent_cls}' not found.")
    
    agent = AgentCls(llm=llm)
    controller = AgentController(agent, workdir=args.directory, max_iterations=args.max_iterations)

    await controller.start_loop(task)

if __name__ == "__main__":
    asyncio.run(main())
