"""Module for a Dummy agent."""

from opendevin.action.base import NullAction
from opendevin.state import State
from opendevin.action import Action
from typing import List
from opendevin.agent import Agent
from opendevin.controller.agent_controller import AgentController
from opendevin.observation.base import NullObservation, Observation

class DummyAgent(Agent):
    """A dummy agent that does nothing but can be used in testing."""

    async def run(self, controller: AgentController) -> Observation:
        return NullObservation('')

    def step(self, state: State) -> Action:
        return NullAction('')

    def search_memory(self, query: str) -> List[str]:
        return []
