from opendevin.controller.agent import Agent

from .riskcalc_agent import RiskCalcAgent

Agent.register('RiskCalcAgent', RiskCalcAgent)
