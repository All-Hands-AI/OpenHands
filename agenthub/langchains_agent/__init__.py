from typing import List

from opendevin.llm.llm import LLM
from opendevin.agent import Agent
from opendevin.state import State
from opendevin.action import Action
import agenthub.langchains_agent.utils.prompts as prompts
from agenthub.langchains_agent.utils.monologue import Monologue
from agenthub.langchains_agent.utils.memory import LongTermMemory

from opendevin.action import (
    ACTION_TYPE_TO_CLASS,
    # NullAction,
    # CmdRunAction,
    # CmdKillAction,
    # BrowseURLAction,
    # FileReadAction,
    # FileWriteAction,
    # AgentRecallAction,
    # AgentThinkAction,
    # AgentFinishAction,
)

# from opendevin.observation import (
#     CmdOutputObservation,
# )


MAX_MONOLOGUE_LENGTH = 20000
MAX_OUTPUT_LENGTH = 5000

INITIAL_THOUGHTS = [
    "I exist!",
    "Hmm...looks like I can type in a command line prompt",
    "Looks like I have a web browser too!",
    "Here's what I want to do: $TASK",
    "How am I going to get there though?",
    "It seems like I have some kind of short term memory.",
    "Each of my thoughts seems to be stored in a numbered list.",
    "It seems whatever I say next will be added to the list.",
    "But no one has perfect short-term memory. My list of thoughts will be summarized and condensed over time, losing information in the process.",
    "Fortunately I have long term memory!",
    "I can just say RECALL, followed by the thing I want to remember. And then related thoughts just spill out!",
    "Sometimes they're random thoughts that don't really have to do with what I wanted to remember. But usually they're exactly what I need!",
    "Let's try it out!",
    "RECALL what it is I want to do",
    "Here's what I want to do: $TASK",
    "How am I going to get there though?",
    "Neat! And it looks like it's easy for me to use the command line too! I just have to say RUN followed by the command I want to run. The command output just jumps into my head!",
    'RUN echo "hello world"',
    "hello world",
    "Cool! I bet I can read and edit files too.",
    "RUN echo \"console.log('hello world')\" > test.js",
    "",
    "I just created test.js. I'll try and run it now.",
    "RUN node test.js",
    "hello world",
    "it works!",
    "And if I want to use the browser, I just need to say BROWSE, followed by a website I want to visit, or an action I want to take on the current site",
    "Let's try that...",
    "BROWSE google.com",
    '<form><input type="text"></input><button type="submit"></button></form>',
    "Very cool. Now to accomplish my task.",
    "I'll need a strategy. And as I make progress, I'll need to keep refining that strategy. I'll need to set goals, and break them into sub-goals.",
    "In between actions, I must always take some time to think, strategize, and set new goals. I should never take two actions in a row.",
    "OK so my task is to $TASK. I haven't made any progress yet. Where should I start?",
    "It seems like there might be an existing project here. I should probably start by running `ls` to see what's here.",
]


MAX_OUTPUT_LENGTH = 5000
MAX_MONOLOGUE_LENGTH = 20000

def action_class_dispatch_initializer(action: str, *arguments: str) -> Action:
    action_class = ACTION_TYPE_TO_CLASS.get(action)
    if action_class is None:
        raise KeyError(f"'{action=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}")
    return action_class(*arguments)

class LangchainsAgent(Agent):
    _initialized = False

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.monologue = Monologue()
        self.memory = LongTermMemory()

    def _add_event(self, event: dict):
        if 'output' in event['args'] and len(event['args']['output']) > MAX_OUTPUT_LENGTH:
            event['args']['output'] = event['args']['output'][:MAX_OUTPUT_LENGTH] + "..."

        self.monologue.add_event(event)
        self.memory.add_event(event)
        if self.monologue.get_total_length() > MAX_MONOLOGUE_LENGTH:
            self.monologue.condense(self.llm)

    def _initialize(self):
        if self._initialized:
            return

        if self.instruction is None or self.instruction == "":
            raise ValueError("Instruction must be provided")
        self.monologue = Monologue()
        self.memory = LongTermMemory()

        next_is_output = False
        for thought in INITIAL_THOUGHTS:
            thought = thought.replace("$TASK", self.instruction)
            if next_is_output:
                self._add_event({"action": "output", "args": {"output": thought}})
                next_is_output = False
            else:
                action, _, argument = thought.partition(" ")
                d = action_class_dispatch_initializer(action, argument)
                self._add_event(d.to_dict())
                next_is_output = True
        self._initialized = True

    def step(self, state: State) -> Action:
        self._initialize()
        # TODO: make langchains agent use Action & Observation
        # completly from ground up

        # Translate state to action_dict
        for prev_action, obs in state.updated_info:
            self._add_event(obs.to_dict())
            self._add_event(prev_action.to_dict())

        state.updated_info = []

        prompt = prompts.get_request_action_prompt(
            self.instruction,
            self.monologue.get_thoughts(),
            state.background_commands_obs,
        )
        messages = [{"content": prompt,"role": "user"}]
        resp = self.llm.completion(messages=messages)
        action_resp = resp['choices'][0]['message']['content']
        action = prompts.parse_action_response(action_resp)
        self.latest_action = action
        return action

    def search_memory(self, query: str) -> List[str]:
        return self.memory.search(query)


Agent.register("LangchainsAgent", LangchainsAgent)
