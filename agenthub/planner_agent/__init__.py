from opendevin.controller.agent import Agent

from .agent import PlannerAgent

Agent.register('PlannerAgent', PlannerAgent)
