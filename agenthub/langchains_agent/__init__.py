import os
import argparse

from opendevin.agent import Agent, Message

from agenthub.langchains_agent.utils.agent import Agent as LangchainsAgentImpl
from agenthub.langchains_agent.utils.event import Event

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

    def _run_loop(self, agent: LangchainsAgentImpl, max_iterations=100):
        # TODO: make it add a Message to the history for each turn / event
        for i in range(max_iterations):
            print("STEP", i, flush=True)
            log_events = agent.get_background_logs()
            for event in log_events:
                print(event, flush=True)
            action = agent.get_next_action()
            if action.action == "finish":
                print("Done!", flush=True)
                break
            print(action, flush=True)
            print("---", flush=True)
            out = agent.maybe_perform_latest_action()
            print(out, flush=True)
            print("==============", flush=True)

    def run(self) -> None:
        """
        Starts the execution of the assigned instruction. This method should
        be implemented by subclasses to define the specific execution logic.
        """
        agent = LangchainsAgentImpl(self.instruction)
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

            agent.add_event(event)
        self._run_loop(agent, self.max_steps)

        # Set the agent's completion status to True
        self._complete = True

    def chat(self, message: str) -> None:
        """
        Optional method for interactive communication with the agent during its execution. Implementations
        can use this method to modify the agent's behavior or state based on chat inputs.

        Parameters:
        - message (str): The chat message or command.
        """
        raise NotImplementedError

Agent.register("LangchainsAgent", LangchainsAgent)
