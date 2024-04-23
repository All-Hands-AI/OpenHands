from opendevin.agent import Agent
from .agent import DummyAgent

Agent.register('DummyAgent', DummyAgent)
