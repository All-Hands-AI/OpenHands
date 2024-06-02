from opendevin.controller.agent import Agent

from .codeact_swe_agent import CodeActSWEAgent

Agent.register('CodeActSWEAgent', CodeActSWEAgent)
