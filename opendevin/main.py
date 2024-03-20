import os
import argparse

import agenthub  # for the agent registry
from opendevin.agent import Agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an agent with a specific task")
    parser.add_argument("-d", "--directory", required=True, type=str, help="The working directory for the agent")
    parser.add_argument("-t", "--task", required=True, type=str, help="The task for the agent to perform")
    parser.add_argument("-c", "--agent-cls", default="LangchainsAgent", type=str, help="The agent class to use")
    args = parser.parse_args()

    print("Working in directory:", args.directory)
    os.chdir(args.directory)

    agent = Agent.create_instance(args.agent_cls, args.task)
    agent.run()
