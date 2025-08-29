from openhands.agenthub.readonly_agent.readonly_agent import ReadOnlyPlanningAgent
from openhands.controller.agent import Agent

Agent.register('ReadOnlyPlanningAgent', ReadOnlyPlanningAgent)
# Backward-compat alias for tests and existing references
Agent.register('ReadOnlyAgent', ReadOnlyPlanningAgent)
