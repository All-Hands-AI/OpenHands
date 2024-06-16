from opendevin.controller.agent import Agent

from .gptswarm_agent import GPTSwarm

Agent.register('GPTSwarmAgent', GPTSwarm)
