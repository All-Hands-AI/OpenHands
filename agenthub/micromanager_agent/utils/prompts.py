import re
from json import JSONDecodeError
from typing import List, Tuple

from opendevin.core import config
from opendevin.core.exceptions import LLMOutputError
from opendevin.core.schema.config import ConfigType
from opendevin.events.action import (
    Action,
    action_from_dict,
)
from opendevin.events.observation import (
    CmdOutputObservation,
)

from . import json

ACTION_PROMPT = """
You're a thoughtful robot. Your main task is this:
%(task)s

Don't expand the scope of your task--just complete it as written.

This is a summary of what you've done thusfar to achieve this goal, and how you've interpreted the outcomes , in JSON format:

%(working memory snippet)s

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
  * `id` - the ID of the background command to kill
* `browse` - opens a web page. Arguments:
  * `url` - the URL to open
* `push` - Push a branch from the current repo to github:
  * `owner` - the owner of the repo to push to
  * `repo` - the name of the repo to push to
  * `branch` - the name of the branch to push
* `recall` - recalls a past memory. Arguments:
  * `query` - the query to search for
* `think` - make a plan, set a goal, or record your thoughts. Arguments:
  * `thought` - the thought to record
* `finish` - if you're absolutely certain that you've completed your task and have tested your work, use the finish action to stop working.

%(background_commands)s

You MUST take time to think in between read, write, run, browse, push, and recall actions.
You should never act twice in a row without thinking. But if your last several
actions are all "think" actions, you should consider taking a different action.

Notes:
* you are logged in as %(user)s, but sudo will always work without a password.
* all non-background commands will be forcibly stopped if they remain running for over %(timeout)s seconds.
* your environment is Debian Linux. You can install software with `sudo apt-get`, but remember to use -y.
* don't run interactive commands, or commands that don't return (e.g. `node server.js`). You may run commands in the background (e.g. `node server.js &`)
* don't run interactive text editors (e.g. `nano` or 'vim'), instead use the 'write' or 'read' action.
* don't run gui applications (e.g. software IDEs (like vs code or codium), web browsers (like firefox or chromium), or other complex software packages). Use non-interactive cli applications, or special actions instead.
* whenever an action fails, always `think` about why it may have happened before acting again.

What is your next single thought or action? Again, you must reply with JSON, and only with JSON. You must respond with exactly one 'action' object.
"""

ORIENT_TO_WORKING_MEMORY_PROMPT = """"
# Premise
You are an AI assistant that acts and perceives according to John Boyd's OODA loop method.
You have just taken the following action:
%(action)s
Which resulted in the following observation:
%(observation)s

Before that action, you had the Actions, Observations, and Orientations:
%(recent_event_log)s

You were working towards the following Subplan:
%(working_subplan)s
And the following Subgoal:
%(working_subgoal)s

# Objective
Based on the action and observation provided, what should your next orientation be?
Additionally, if the action and observation suggest either a new subplan or subgoal, please provide those as well.
    - If no new subplan or subgoal is suggested, you can add an empty string for the field.
## Response Format
Your response must be in JSON format.
Your response must contain three fields:
* `orientation` - The next orientation you should take
* `new_subplan` - The new subplan you should work towards. This can be an empty string.
* `new_subgoal` - The new subgoal you should work towards. This can be an empty string.

What are your next orientation, new subplan, and new subgoal?
"""


### Working Memory Prompts ###
def get_orient_to_working_memory_prompt(action, observation, recent_event_log, working_subplan, working_subgoal):
    return ORIENT_TO_WORKING_MEMORY_PROMPT % {
        'action': action,
        'observation': observation,
        'recent_event_log': json.dumps(recent_event_log, indent=2),
        'working_subplan': working_subplan,
        'working_subgoal': working_subgoal
    }

def parse_orient_response(response: str) -> Tuple[str, str, str]:
    """
    Parses a string to find an action within it, specifically looking for keys 'orientation', 'new_subplan', and 'new_subgoal'.

    Parameters:
    - response (str): The string to be parsed

    Returns:
    - Action: The action that was found in the response string
    """
    try:
        orientation_dict: dict = json.loads(response)
    except JSONDecodeError:
        # Find response-looking json in the output and use the more promising one. Helps with weak llms
        response_json_matches = re.finditer(
            r"""{\s*\"orientation\":\s?\"(\w+)\"(?:,?|,\s*\"new_subplan\":\s?\"((?:.|\s)*?)\"(?:,?|,\s*\"new_subgoal\":\s?\"((?:.|\s)*?)\")\s*}""",
            response,
        )  # Find all response-looking strings

        def rank(match):
            # Rank responses by the presence and length of 'new_subplan' and 'new_subgoal'
            subplan_length = len(match.group(2)) if match.group(2) else 0
            subgoal_length = len(match.group(3)) if match.group(3) else 0
            return subplan_length + subgoal_length

        try:
            orientation_dict: dict = json.loads(
                max(response_json_matches, key=rank).group(0)
            )  # Use the highest ranked response
        except (ValueError, JSONDecodeError):
            raise LLMOutputError(
                'Invalid JSON, the response must be well-formed JSON as specified in the prompt.'
            )
    except (ValueError, TypeError):
        raise LLMOutputError(
            'Invalid JSON, the response must be well-formed JSON as specified in the prompt.'
        )
    
    if len(orientation_dict['new_subplan']) < 10:
        orientation_dict['new_subplan'] = None
    if len(orientation_dict['new_subgoal']) < 10:
        orientation_dict['new_subgoal'] = None
    
    return orientation_dict['orientation'], orientation_dict['new_subplan'], orientation_dict['new_subgoal']


### Core Agent Prompts ###

def get_request_action_prompt(
    task: str,
    working_memory_rendered: str,
    background_commands_obs: List[CmdOutputObservation] = [],
):
    """
    Gets the action prompt formatted with appropriate values.

    Parameters:
    - task (str): The current task the agent is trying to accomplish
    - thoughts (List[dict]): The agent's current thoughts
    - background_commands_obs (List[CmdOutputObservation]): List of all observed background commands running

    Returns:
    - str: Formatted prompt string with hint, task, monologue, and background included
    """

    # hint = ''
    # if len(thoughts) > 0:
    #     latest_thought = thoughts[-1]
    #     if 'action' in latest_thought:
    #         if latest_thought['action'] == 'think':
    #             if latest_thought['args']['thought'].startswith('OK so my task is'):
    #                 hint = "You're just getting started! What should you do first?"
    #             else:
    #                 hint = "You've been thinking a lot lately. Maybe it's time to take action?"
    #         elif latest_thought['action'] == 'error':
    #             hint = 'Looks like that last command failed. Maybe you need to fix it, or try something else.'

    bg_commands_message = ''
    if len(background_commands_obs) > 0:
        bg_commands_message = 'The following commands are running in the background:'
        for command_obs in background_commands_obs:
            bg_commands_message += (
                f'\n`{command_obs.command_id}`: {command_obs.command}'
            )
        bg_commands_message += '\nYou can end any process by sending a `kill` action with the numerical `id` above.'

    user = 'opendevin' if config.get(ConfigType.RUN_AS_DEVIN) else 'root'

    return ACTION_PROMPT % {
        'task': task,
        'working_memory_snippet': working_memory_rendered,#json.dumps(thoughts, indent=2),
        'background_commands': bg_commands_message,
        'user': user,
        'timeout': config.get(ConfigType.SANDBOX_TIMEOUT),
        'WORKSPACE_MOUNT_PATH_IN_SANDBOX': config.get(
            ConfigType.WORKSPACE_MOUNT_PATH_IN_SANDBOX
        ),
    }

def parse_action_response(response: str) -> Action:
    """
    Parses a string to find an action within it

    Parameters:
    - response (str): The string to be parsed

    Returns:
    - Action: The action that was found in the response string
    """
    try:
        action_dict = json.loads(response)
    except JSONDecodeError:
        # Find response-looking json in the output and use the more promising one. Helps with weak llms
        response_json_matches = re.finditer(
            r"""{\s*\"action\":\s?\"(\w+)\"(?:,?|,\s*\"args\":\s?{((?:.|\s)*?)})\s*}""",
            response,
        )  # Find all response-looking strings

        def rank(match):
            return (
                len(match[2]) if match[1] == 'think' else 130
            )  # Crudely rank multiple responses by length

        try:
            action_dict = json.loads(
                max(response_json_matches, key=rank)[0]
            )  # Use the highest ranked response
        except (ValueError, JSONDecodeError):
            raise LLMOutputError(
                'Invalid JSON, the response must be well-formed JSON as specified in the prompt.'
            )
    except (ValueError, TypeError):
        raise LLMOutputError(
            'Invalid JSON, the response must be well-formed JSON as specified in the prompt.'
        )
    if 'content' in action_dict:
        # The LLM gets confused here. Might as well be robust
        action_dict['contents'] = action_dict.pop('content')
    return action_from_dict(action_dict)