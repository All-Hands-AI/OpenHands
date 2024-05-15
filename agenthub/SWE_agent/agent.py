from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import (
    Action,
    FileReadAction,
    FileWriteAction,
    MessageAction,
)
from opendevin.events.observation import Observation
from opendevin.events.serialization.event import event_to_memory
from opendevin.llm.llm import LLM

from .parser import parse_command
from .prompts import (
    CONTEXT_PROMPT,
    MEMORY_FORMAT,
    NO_ACTION,
    STEP_PROMPT,
    SYSTEM_MESSAGE,
)


class SWEAgent(Agent):
    """
    An attempt to recreate swe_agent with output parsing, prompting style, and Application Computer Interface (ACI).

    SWE-agent includes ACI functions like 'goto', 'search_for', 'edit', 'scroll', 'run'
    """

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.memory_window = 4
        self.max_retries = 2
        self.running_memory: list[str] = []
        self.cur_file: str = ''
        self.cur_line: int = 0

    def _remember(self, action: Action, observation: Observation) -> None:
        """Agent has a limited memory of the few steps implemented as a queue"""
        memory = MEMORY_FORMAT(event_to_memory(action), event_to_memory(observation))
        self.running_memory.append(memory)

    def _think_act(self, messages: list[dict]) -> tuple[Action, str]:
        resp = self.llm.completion(
            messages=messages,
            temperature=0.05,
        )
        action_resp = resp['choices'][0]['message']['content']
        print(f"\033[1m\033[91m{resp['usage']}\033[0m")
        print(
            '\n==== RAW OUTPUT ====',
            f'\033[96m{action_resp}\033[0m',
            '==== END RAW ====\n',
            sep='\n',
        )
        return parse_command(action_resp, self.cur_file, self.cur_line)

    def _update(self, action: Action) -> None:
        if isinstance(action, (FileReadAction, FileWriteAction)):
            self.cur_file = action.path
            self.cur_line = action.start

    def step(self, state: State) -> Action:
        """
        SWE-Agent step:
            1. Get context - past actions, custom commands, current step
            2. Perform think-act - prompt model for action and reasoning
            3. Catch errors - ensure model takes action (5 attempts max)
        """
        for prev_action, obs in state.updated_info:
            self._remember(prev_action, obs)

        goal = state.get_current_user_intent()
        prompt = STEP_PROMPT(goal, self.cur_file, self.cur_line)

        msgs = [
            {'content': SYSTEM_MESSAGE, 'role': 'system'},
            {'content': prompt, 'role': 'user'},
        ]

        if len(self.running_memory) > 0:
            context = CONTEXT_PROMPT(self.running_memory, self.memory_window)
            msgs.insert(1, {'content': context, 'role': 'user'})
        # clrs = [''] * (len(msgs)-2) + ['\033[0;36m', '\033[0;35m']
        # print('\n\n'.join([c+m['content']+'\033[0m' for c, m in zip(clrs, msgs)]))
        action, thought = self._think_act(messages=msgs)

        start_msg_len = len(msgs)
        while not action and len(msgs) < self.max_retries + start_msg_len:
            error = NO_ACTION(thought)
            error_msg = {'content': error, 'role': 'user'}
            msgs.append(error_msg)
            action, thought = self._think_act(messages=msgs)

        if not action:
            action = MessageAction(thought)

        self._update(action)
        self.latest_action = action
        return action

    def search_memory(self, query: str) -> list[str]:
        return [item for item in self.running_memory if query in item]

    def reset(self) -> None:
        """Used to reset the agent"""
        self.running_memory = []
        super().reset()
