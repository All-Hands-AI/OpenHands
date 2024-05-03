from opendevin.controller.agent import Agent

from .agent import DelegatorAgent

Agent.register('DelegatorAgent', DelegatorAgent)
