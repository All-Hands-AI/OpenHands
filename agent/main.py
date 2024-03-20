import sys
import os

from lib.agent import Agent
from lib.event import Event
from lib.controlloop import run_loop

if len(sys.argv) < 3:
    print("Usage: python main.py <working_directory> <task>")
    sys.exit(1)

working_directory = sys.argv[1]
task = sys.argv[2]

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
"RUN echo \"hello world\"",
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
"<form><input type=\"text\"></input><button type=\"submit\"></button></form>",
"Very cool. Now to accomplish my task.",
"I'll need a strategy. And as I make progress, I'll need to keep refining that strategy. I'll need to set goals, and break them into sub-goals.",
"In between actions, I must always take some time to think, strategize, and set new goals. I should never take two actions in a row.",
"OK so my task is to $TASK. I haven't made any progress yet. Where should I start?",
"It seems like there might be an existing project here. I should probably start by running `ls` to see what's here.",
]

def main():
    print("Working in directory:", sys.argv[1])
    os.chdir(working_directory)

    agent = Agent(task)
    next_is_output = False
    for thought in INITIAL_THOUGHTS:
        thought = thought.replace("$TASK", task)
        if next_is_output:
            event = Event('output', {'output': thought})
            next_is_output = False
        else:
            if thought.startswith("RUN"):
                command = thought.split("RUN ")[1]
                event = Event('run', {'command': command})
                next_is_output = True
            elif thought.startswith("RECALL"):
                query = thought.split("RECALL ")[1]
                event = Event('recall', {'query': query})
                next_is_output = True
            elif thought.startswith("BROWSE"):
                url = thought.split("BROWSE ")[1]
                event = Event('browse', {'url': url})
                next_is_output = True
            else:
                event = Event('think', {'thought': thought})

        agent.add_event(event)
    run_loop(agent)

if __name__ == "__main__":
    main()

