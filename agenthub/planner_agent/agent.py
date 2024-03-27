from typing import List
from .prompt import get_prompt

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action

class PlannerAgent(Agent):
    def __init__(self, llm: LLM):
        super().__init__(llm)

    def step(self, state: State) -> Action:
        prompt = get_prompt(self.instruction, state.plan, state.history)
        return None

    def search_memory(self, query: str) -> List[str]:
        return []

Agent.register("PlannerAgent", PlannerAgent)
