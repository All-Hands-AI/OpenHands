from opendevin.controller.agent import Agent

from .agent import MicroManagerAgent

Agent.register('MicroManagerAgent', MicroManagerAgent)