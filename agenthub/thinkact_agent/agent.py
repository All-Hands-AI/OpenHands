from typing import List
from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action
from opendevin.observation import Observation

from .parser import parse_command

from .prompts import (
    START_MESSAGE,
    STEP_PROMPT,
    MEMORY_FORMAT
)


class ThinkActAgent(Agent):
    """
    An attempt to recreate swe_agent with output parsing, prompting style, and Application Computer Interface.

    SWE-agent includes ACI functions like 'goto', 'search_for', 'edit', 'scroll', 'run'
    """

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.running_memory: List[str] = []

    def _remember(self, action: Action, observation: Observation):
        memory = MEMORY_FORMAT(action.to_dict(), observation.to_dict())
        self.running_memory.append(memory)

    def step(self, state: State) -> Action:

        for prev_action, obs in state.updated_info:
            self._remember(prev_action, obs)

        prompt = STEP_PROMPT(
            state.iteration,
            state.plan.get_current_task(),
            state.working_dir,
            state.file_name,
            '\n\n'.join(t for t in self.running_memory)
        )

        messages = [
            {'content': prompt, 'role': 'user'},
            {'content': START_MESSAGE, 'role': 'user'}
        ]

        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        action, thought = parse_command(action_resp)
        self.latest_action = action
        return action

    def search_memory(self, query: str) -> List[str]:
        return [item for item in self.running_memory if query in item]

    def reset(self) -> None:
        """Used to reset the agent"""
        self.running_memory = []
        super().reset()
