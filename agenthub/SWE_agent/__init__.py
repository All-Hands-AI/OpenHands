from opendevin.controller.agent import Agent

from .agent import SWEAgent

Agent.register('SWEAgent', SWEAgent)
