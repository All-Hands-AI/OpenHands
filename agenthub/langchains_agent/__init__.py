from typing import List, Dict, Type

import agenthub.langchains_agent.utils.llm as llm
from opendevin.agent import Agent
from opendevin.action import (
    Action,
    CmdRunAction,
    CmdKillAction,
    BrowseURLAction,
    FileReadAction,
    FileWriteAction,
    AgentRecallAction,
    AgentThinkAction,
    AgentFinishAction,
)
from opendevin.observation import (
    Observation,
    CmdOutputObservation,
    UserMessageObservation,
    AgentMessageObservation,
    BrowserOutputObservation,
)
from opendevin.state import State

from agenthub.langchains_agent.utils.monologue import Monologue
from agenthub.langchains_agent.utils.memory import LongTermMemory


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


ACTION_TYPE_TO_CLASS: Dict[str, Type[Action]] = {
    "run": CmdRunAction,
    "kill": CmdKillAction,
    "browse": BrowseURLAction,
    "read": FileReadAction,
    "write": FileWriteAction,
    "recall": AgentRecallAction,
    "think": AgentThinkAction,
    "finish": AgentFinishAction,
}


class LangchainsAgent(Agent):
    _initialized = False

    def __init__(self, instruction: str, model_name: str):
        super().__init__(instruction, model_name)
        self.monologue = Monologue(self.model_name)
        self.memory = LongTermMemory()

    def _update_memory(self, info: Action | Observation):
        self.monologue.add_event(info)
        self.memory.add_event(info)
        if self.monologue.get_total_length() > MAX_MONOLOGUE_LENGTH:
            self.monologue.condense()

    def _initialize(self):
        if self._initialized:
            return
        next_is_output = False
        next_output_type = None
        for thought in INITIAL_THOUGHTS:
            thought = thought.replace("$TASK", self.instruction)
            if next_is_output:
                d = next_output_type(contnet=thought)

                next_is_output = False
                next_output_type = None
            else:
                if thought.startswith("RUN"):
                    command = thought.split("RUN ")[1]
                    d = CmdRunAction(command=command)

                    next_is_output = True
                    next_output_type = CmdOutputObservation

                elif thought.startswith("RECALL"):
                    query = thought.split("RECALL ")[1]
                    d = AgentRecallAction(query=query)
                    next_is_output = True
                    next_output_type = AgentMessageObservation

                elif thought.startswith("BROWSE"):
                    url = thought.split("BROWSE ")[1]
                    d = BrowseURLAction(url=url)
                    next_is_output = True
                    next_output_type = BrowserOutputObservation
                else:
                    d = AgentThinkAction(thought=thought)

        self._update_memory(d)
        self._initialized = True

    def step(self, state: State) -> Action:
        self._initialize()
        action_dict = llm.request_action(
            self.instruction,
            self.monologue.get_thoughts(),
            self.model_name,
            state.background_commands,
        )
        action = ACTION_TYPE_TO_CLASS[action_dict["action"]](**action_dict["args"])
        self.latest_action = action
        return action

    def search_memory(self, query: str) -> List[str]:
        return self.memory.search(query)


Agent.register("LangchainsAgent", LangchainsAgent)
