import os
import argparse

import agenthub  # for the agent registry
from opendevin.agent import Agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an agent with a specific task")
    parser.add_argument("-d", "--directory", required=True, type=str, help="The working directory for the agent")
    parser.add_argument("-t", "--task", required=True, type=str, help="The task for the agent to perform")
    parser.add_argument("-c", "--agent-cls", default="LangchainsAgent", type=str, help="The agent class to use")
    parser.add_argument("-m", "--model-name", default="gpt-3.5-turbo-0125", type=str, help="The (litellm) model name to use")
    args = parser.parse_args()

    AgentCls: Agent = Agent.get_cls(args.agent_cls)
    agent = AgentCls(
        instruction=args.task,
        workspace_dir=args.directory,
        model_name=args.model_name
    )
    agent.run()
