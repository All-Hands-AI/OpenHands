from opendevin.controller.agent import Agent

from .browsing_agent import BrowsingAgent

Agent.register('BrowsingAgent', BrowsingAgent)
