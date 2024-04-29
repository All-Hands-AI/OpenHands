"""Module for a Dummy agent."""

from typing import List

from opendevin.action import Action
from opendevin.action.base import NullAction
from opendevin.agent import Agent
from opendevin.controller.agent_controller import AgentController
from opendevin.observation.base import NullObservation, Observation
from opendevin.state import State


class DummyAgent(Agent):
    """A dummy agent that does nothing but can be used in testing."""

    async def run(self, controller: AgentController) -> Observation:
        return NullObservation('')

    def step(self, state: State) -> Action:
        return NullAction('')

    def search_memory(self, query: str) -> List[str]:
        return []
