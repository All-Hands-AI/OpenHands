"""TomCodeActAgent module - CodeAct Agent with Tom integration."""

from openhands.agenthub.tom_codeact_agent.tom_codeact_agent import TomCodeActAgent
from openhands.controller.agent import Agent

# Register the agent
Agent.register('TomCodeActAgent', TomCodeActAgent)

__all__ = ['TomCodeActAgent']