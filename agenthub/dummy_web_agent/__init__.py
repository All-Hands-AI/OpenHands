from opendevin.controller.agent import Agent

from .dummy_web_agent import DummyWebAgent

Agent.register('DummyWebAgent', DummyWebAgent)
