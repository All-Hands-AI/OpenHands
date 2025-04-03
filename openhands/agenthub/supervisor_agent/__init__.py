from openhands.agenthub.supervisor_agent.supervisor_agent import SupervisorAgent
from openhands.controller.agent import Agent

Agent.register('SupervisorAgent', SupervisorAgent)

__all__ = ['SupervisorAgent']
