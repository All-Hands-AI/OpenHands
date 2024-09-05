from agenthub.coact_agent.planner.planner_agent import (
    GlobalPlannerAgent as CoActPlannerAgent,
)
from openhands.controller.agent import Agent

Agent.register('CoActPlannerAgent', CoActPlannerAgent)
