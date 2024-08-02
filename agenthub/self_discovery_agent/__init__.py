from opendevin.controller.agent import Agent

from .agent import SelfDiscoveryAgent

Agent.register('SelfDiscoveryAgent', SelfDiscoveryAgent)
