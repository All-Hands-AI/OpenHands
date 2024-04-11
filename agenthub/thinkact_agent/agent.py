from typing import List
from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import Action, AgentThinkAction
from opendevin.observation import Observation

from .parser import parse_command

from .prompts import (
    SYSTEM_MESSAGE,
    STEP_PROMPT,
    MEMORY_FORMAT,
    NO_ACTION,
    CONTEXT_PROMPT
)


class ThinkActAgent(Agent):
    """
    An attempt to recreate swe_agent with output parsing, prompting style, and Application Computer Interface (ACI).

    SWE-agent includes ACI functions like 'goto', 'search_for', 'edit', 'scroll', 'run'
    """

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.memory_window = 5
        self.max_retries = 5
        self.running_memory: List[str] = []

    def _remember(self, action: Action, observation: Observation):
        """Agent has a limited memory of the few steps implemented as a queue"""
        memory = MEMORY_FORMAT(action.to_dict(), observation.to_dict())
        self.running_memory.append(memory)

    def _think_act(self, messages: List[dict]) -> tuple[Action, str]:
        resp = self.llm.completion(
            messages=messages,
            temperature=0.0
        )
        action_resp = resp['choices'][0]['message']['content']
        return parse_command(action_resp)

    def step(self, state: State) -> Action:
        """
        SWE-Agent step:
            1. Get context - past actions, custom commands, current step
            2. Perform think-act - prompt model for action and reasoning
            3. Catch errors - ensure model takes action (5 attempts max)
        """
        for prev_action, obs in state.updated_info:
            self._remember(prev_action, obs)

        prompt = STEP_PROMPT(
            state.plan.main_goal,
            state.working_dir,
            state.file_name,
            state.cur_line
        )

        msgs = [
            {'content': SYSTEM_MESSAGE, 'role': 'user'},
            {'content': prompt, 'role': 'user'}
        ]

        if len(self.running_memory) > 0:
            context = CONTEXT_PROMPT(
                self.running_memory,
                self.memory_window
            )
            msgs.insert(0, {'content': context, 'role': 'user'})

        # print('\n\n\n'.join([m['content'] for m in msgs]))
        action, thought = self._think_act(messages=msgs)

        start_msg_len = len(msgs)
        while not action and len(msgs) < self.max_retries + start_msg_len:
            error = NO_ACTION(thought)
            error_msg = {'content': error, 'role': 'user'}
            msgs.append(error_msg)
            action, thought = self._think_act(messages=msgs)

        if not action:
            action = AgentThinkAction(thought)

        self.latest_action = action
        return action

    def search_memory(self, query: str) -> List[str]:
        return [item for item in self.running_memory if query in item]

    def reset(self) -> None:
        """Used to reset the agent"""
        self.running_memory = []
        super().reset()
