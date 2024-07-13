from opendevin.controller.agent import Agent

from .moatless_codeact_agent import MoatlessCodeActAgent
from .moatless_search_agent import MoatlessSearchAgent

Agent.register('MoatlessSearchAgent', MoatlessSearchAgent)
Agent.register('MoatlessCodeActAgent', MoatlessCodeActAgent)
