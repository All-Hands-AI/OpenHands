from opendevin.controller.agent import Agent

from .moatless_search_agent import MoatlessSearchAgent

Agent.register('MoatlessSearchAgent', MoatlessSearchAgent)
