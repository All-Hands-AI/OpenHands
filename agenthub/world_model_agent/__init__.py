from opendevin.controller.agent import Agent

from .world_model_agent import WorldModelAgent

Agent.register('WorldModelAgent', WorldModelAgent)
