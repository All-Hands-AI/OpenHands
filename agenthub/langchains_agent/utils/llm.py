import os

from . import json

if os.getenv("DEBUG"):
    from langchain.globals import set_debug
    set_debug(True)

from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

ACTION_PROMPT = """
You're a thoughtful robot. Your main task is to {task}.
Don't expand the scope of your task--just complete it as written.

This is your internal monologue, in JSON format:
```json
{monologue}
```

Your most recent thought is at the bottom of that monologue. Continue your train of thought.
What is your next thought or action? Your response must be in JSON format.
It must be an object, and it must contain two fields:
* `action`, which is one of the actions below
* `args`, which is a map of key-value pairs, specifying the arguments for that action

Here are the possible actions:
* `read` - reads the contents of a file. Arguments:
  * `path` - the path of the file to read
* `write` - writes the contents to a file. Arguments:
  * `path` - the path of the file to write
  * `contents` - the contents to write to the file
* `run` - runs a command. Arguments:
  * `command` - the command to run
  * `background` - if true, run the command in the background, so that other commands can be run concurrently. Useful for e.g. starting a server. You won't be able to see the logs. You don't need to end the command with `&`, just set this to true.
* `kill` - kills a background command
  * `id` - the ID of the background command to kill
* `browse` - opens a web page. Arguments:
  * `url` - the URL to open
* `recall` - recalls a past memory. Arguments:
  * `query` - the query to search for
* `think` - make a plan, set a goal, or record your thoughts. Arguments:
  * `thought` - the thought to record
* `finish` - if you're absolutely certain that you've completed your task and have tested your work, use the finish action to stop working.

{background_commands}

You MUST take time to think in between read, write, run, browse, and recall actions.
You should never act twice in a row without thinking. But if your last several
actions are all "think" actions, you should consider taking a different action.

Notes:
* your environment is Debian Linux. You can install software with `apt`
* you can use `git commit` to stash your work, but you don't have access to a remote repository
* your working directory will not change, even if you run `cd`. All commands will be run in the `/workspace` directory.
* don't run interactive commands, or commands that don't return (e.g. `node server.js`). You may run commands in the background (e.g. `node server.js &`)

What is your next thought or action? Again, you must reply with JSON, and only with JSON.

{hint}
"""

MONOLOGUE_SUMMARY_PROMPT = """
Below is the internal monologue of an automated LLM agent. Each
thought is an item in a JSON array. The thoughts may be memories,
actions taken by the agent, or outputs from those actions.
Please return a new, smaller JSON array, which summarizes the
internal monologue. You can summarize individual thoughts, and
you can condense related thoughts together with a description
of their content.
```json
{monologue}
```
Make the summaries as pithy and informative as possible.
Be specific about what happened and what was learned. The summary
will be used as keywords for searching for the original memory.
Be sure to preserve any key words or important information.

Your response must be in JSON format. It must be an object with the
key `new_monologue`, which is a JSON array containing the summarized monologue.
Each entry in the array must have an `action` key, and an `args` key.
The action key may be `summarize`, and `args.summary` should contain the summary.
You can also use the same action and args from the source monologue.
"""

class Action(BaseModel):
    action: str
    args: dict

class NewMonologue(BaseModel):
    new_monologue: List[Action]

def get_chain(template):
    llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), model_name=os.getenv("OPENAI_MODEL"))
    prompt = PromptTemplate.from_template(template)
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    return llm_chain

def summarize_monologue(thoughts):
    llm_chain = get_chain(MONOLOGUE_SUMMARY_PROMPT)
    parser = JsonOutputParser(pydantic_object=NewMonologue)
    resp = llm_chain.invoke({'monologue': json.dumps({'old_monologue': thoughts})})
    if os.getenv("DEBUG"):
        print("resp", resp)
    parsed = parser.parse(resp['text'])
    return parsed['new_monologue']

def request_action(task, thoughts, background_commands=[]):
    llm_chain = get_chain(ACTION_PROMPT)
    parser = JsonOutputParser(pydantic_object=Action)
    hint = ''
    if len(thoughts) > 0:
        latest_thought = thoughts[-1]
        if latest_thought.action == 'think':
            if latest_thought.args['thought'].startswith("OK so my task is"):
                hint = "You're just getting started! What should you do first?"
            else:
                hint = "You've been thinking a lot lately. Maybe it's time to take action?"
        elif latest_thought.action == 'error':
            hint = "Looks like that last command failed. Maybe you need to fix it, or try something else."

    bg_commands_message = ""
    if len(background_commands) > 0:
        bg_commands_message = "The following commands are running in the background:"
        for id, command in background_commands.items():
            bg_commands_message += f"\n`{id}`: {command.command}"
        bg_commands_message += "\nYou can end any process by sending a `kill` action with the numerical `id` above."

    latest_thought = thoughts[-1]
    resp = llm_chain.invoke({
        "monologue": json.dumps(thoughts),
        "hint": hint,
        "task": task,
        "background_commands": bg_commands_message,
    })
    if os.getenv("DEBUG"):
        print("resp", resp)
    parsed = parser.parse(resp['text'])
    return parsed


