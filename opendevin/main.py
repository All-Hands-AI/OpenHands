import argparse

import agenthub  # for the agent registry
from opendevin.agent import Agent
from opendevin.controller import AgentController

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an agent with a specific task")
    parser.add_argument("-d", "--directory", required=True, type=str, help="The working directory for the agent")
    parser.add_argument("-t", "--task", required=True, type=str, help="The task for the agent to perform")
    parser.add_argument("-c", "--agent-cls", default="LangchainsAgent", type=str, help="The agent class to use")
    parser.add_argument("-m", "--model-name", default="gpt-4-0125-preview", type=str, help="The (litellm) model name to use")
    args = parser.parse_args()

    print(f"Running agent {args.agent_cls} (model: {args.model_name}, directory: {args.directory}) with task: \"{args.task}\"")

    AgentCls: Agent = Agent.get_cls(args.agent_cls)
    agent = AgentCls(
        instruction=args.task,
        workspace_dir=args.directory,
        model_name=args.model_name
    )

    controller = AgentController(agent, args.directory)
    controller.start_loop()
