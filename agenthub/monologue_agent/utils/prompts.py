from opendevin.core.config import config
from opendevin.core.utils import json
from opendevin.events.action import (
    Action,
)
from opendevin.events.observation import (
    CmdOutputObservation,
)
from opendevin.events.serialization.action import action_from_dict

ACTION_PROMPT = """
You're a thoughtful robot. Your main task is this:
%(task)s

Don't expand the scope of your task--just complete it as written.

This is your internal monologue, in JSON format:

%(monologue)s


Your most recent thought is at the bottom of that monologue. Continue your train of thought.
What is your next single thought or action? Your response must be in JSON format.
It must be a single object, and it must contain two fields:
* `action`, which is one of the actions below
* `args`, which is a map of key-value pairs, specifying the arguments for that action

Here are the possible actions:
* `read` - reads the content of a file. Arguments:
  * `path` - the path of the file to read
* `write` - writes the content to a file. Arguments:
  * `path` - the path of the file to write
  * `content` - the content to write to the file
* `run` - runs a command. Arguments:
  * `command` - the command to run
  * `background` - if true, run the command in the background, so that other commands can be run concurrently. Useful for e.g. starting a server. You won't be able to see the logs. You don't need to end the command with `&`, just set this to true.
* `kill` - kills a background command
  * `command_id` - the ID of the background command to kill
* `browse` - opens a web page. Arguments:
  * `url` - the URL to open
* `push` - Push a branch from the current repo to github:
  * `owner` - the owner of the repo to push to
  * `repo` - the name of the repo to push to
  * `branch` - the name of the branch to push
* `recall` - recalls a past memory. Arguments:
  * `query` - the query to search for
* `message` - make a plan, set a goal, or record your thoughts. Arguments:
  * `content` - the message to record
* `finish` - if you're absolutely certain that you've completed your task and have tested your work, use the finish action to stop working.

%(background_commands)s

You MUST take time to think in between read, write, run, browse, push, and recall actions--do this with the `message` action.
You should never act twice in a row without thinking. But if your last several
actions are all `message` actions, you should consider taking a different action.

Notes:
* you are logged in as %(user)s, but sudo will always work without a password.
* all non-background commands will be forcibly stopped if they remain running for over %(timeout)s seconds.
* your environment is Debian Linux. You can install software with `sudo apt-get`, but remember to use -y.
* don't run interactive commands, or commands that don't return (e.g. `node server.js`). You may run commands in the background (e.g. `node server.js &`)
* don't run interactive text editors (e.g. `nano` or 'vim'), instead use the 'write' or 'read' action.
* don't run gui applications (e.g. software IDEs (like vs code or codium), web browsers (like firefox or chromium), or other complex software packages). Use non-interactive cli applications, or special actions instead.
* whenever an action fails, always send a `message` about why it may have happened before acting again.

What is your next single thought or action? Again, you must reply with JSON, and only with JSON. You must respond with exactly one 'action' object.

%(hint)s
"""

MONOLOGUE_SUMMARY_PROMPT = """
Below is the internal monologue of an automated LLM agent. Each
thought is an item in a JSON array. The thoughts may be memories,
actions taken by the agent, or outputs from those actions.
Please return a new, smaller JSON array, which summarizes the
internal monologue. You can summarize individual thoughts, and
you can condense related thoughts together with a description
of their content.

%(monologue)s

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


def get_summarize_monologue_prompt(thoughts: list[dict]):
    """
    Gets the prompt for summarizing the monologue

    Returns:
    - str: A formatted string with the current monologue within the prompt
    """
    return MONOLOGUE_SUMMARY_PROMPT % {
        'monologue': json.dumps({'old_monologue': thoughts}, indent=2),
    }


def get_request_action_prompt(
    task: str,
    thoughts: list[dict],
    background_commands_obs: list[CmdOutputObservation] = [],
):
    """
    Gets the action prompt formatted with appropriate values.

    Parameters:
    - task (str): The current task the agent is trying to accomplish
    - thoughts (list[dict]): The agent's current thoughts
    - background_commands_obs (list[CmdOutputObservation]): list of all observed background commands running

    Returns:
    - str: Formatted prompt string with hint, task, monologue, and background included
    """

    hint = ''
    if len(thoughts) > 0:
        latest_thought = thoughts[-1]
        if 'action' in latest_thought:
            if latest_thought['action'] == 'message':
                if latest_thought['args']['content'].startswith('OK so my task is'):
                    hint = "You're just getting started! What should you do first?"
                else:
                    hint = "You've been thinking a lot lately. Maybe it's time to take action?"
            elif latest_thought['action'] == 'error':
                hint = 'Looks like that last command failed. Maybe you need to fix it, or try something else.'

    bg_commands_message = ''
    if len(background_commands_obs) > 0:
        bg_commands_message = 'The following commands are running in the background:'
        for command_obs in background_commands_obs:
            bg_commands_message += (
                f'\n`{command_obs.command_id}`: {command_obs.command}'
            )
        bg_commands_message += '\nYou can end any process by sending a `kill` action with the numerical `command_id` above.'

    user = 'opendevin' if config.run_as_devin else 'root'

    return ACTION_PROMPT % {
        'task': task,
        'monologue': json.dumps(thoughts, indent=2),
        'background_commands': bg_commands_message,
        'hint': hint,
        'user': user,
        'timeout': config.sandbox_timeout,
        'WORKSPACE_MOUNT_PATH_IN_SANDBOX': config.workspace_mount_path_in_sandbox,
    }


def parse_action_response(orig_response: str) -> Action:
    """
    Parses a string to find an action within it

    Parameters:
    - response (str): The string to be parsed

    Returns:
    - Action: The action that was found in the response string
    """
    # attempt to load the JSON dict from the response
    action_dict = json.loads(orig_response)

    if 'content' in action_dict:
        # The LLM gets confused here. Might as well be robust
        action_dict['contents'] = action_dict.pop('content')

    return action_from_dict(action_dict)


def parse_summary_response(response: str) -> list[dict]:
    """
    Parses a summary of the monologue

    Parameters:
    - response (str): The response string to be parsed

    Returns:
    - list[dict]: The list of summaries output by the model
    """
    parsed = json.loads(response)
    return parsed['new_monologue']
