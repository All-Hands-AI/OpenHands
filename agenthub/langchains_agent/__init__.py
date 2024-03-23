from typing import List

from opendevin.agent import Agent

from agenthub.langchains_agent.utils.agent import Agent as LangchainsAgentImpl
from opendevin.lib.event import Event

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


class LangchainsAgent(Agent):
    _initialized = False

    def _initialize(self):
        if self._initialized:
            return
        self.agent = LangchainsAgentImpl(self.instruction, self.model_name)
        next_is_output = False
        for thought in INITIAL_THOUGHTS:
            thought = thought.replace("$TASK", self.instruction)
            if next_is_output:
                event = Event("output", {"output": thought})
                next_is_output = False
            else:
                if thought.startswith("RUN"):
                    command = thought.split("RUN ")[1]
                    event = Event("run", {"command": command})
                    next_is_output = True
                elif thought.startswith("RECALL"):
                    query = thought.split("RECALL ")[1]
                    event = Event("recall", {"query": query})
                    next_is_output = True
                elif thought.startswith("BROWSE"):
                    url = thought.split("BROWSE ")[1]
                    event = Event("browse", {"url": url})
                    next_is_output = True
                else:
                    event = Event("think", {"thought": thought})
            self.agent.add_event(event)
        self._initialized = True

    def add_event(self, event: Event) -> None:
        self.agent.add_event(event)

    def step(self, cmd_mgr) -> Event:
        self._initialize()
        return self.agent.get_next_action(cmd_mgr)

    def search_memory(self, query: str) -> List[str]:
        return self.agent.memory.search(query)

    def chat(self, message: str) -> None:
        """
        Optional method for interactive communication with the agent during its execution. Implementations
        can use this method to modify the agent's behavior or state based on chat inputs.

        Parameters:
        - message (str): The chat message or command.
        """
        raise NotImplementedError

Agent.register("LangchainsAgent", LangchainsAgent)
