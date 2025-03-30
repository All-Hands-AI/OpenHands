# CodeActReadOnlyAgent module
from openhands.agenthub.codeact_readonly_agent.codeact_readonly_agent import CodeActReadOnlyAgent
from openhands.controller.agent import Agent

Agent.register('CodeActReadOnlyAgent', CodeActReadOnlyAgent)