import json
from typing import Dict, List, Tuple, Type

from opendevin.controller.state.plan import Plan
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ActionType
from opendevin.events.action import (
    Action,
    AddTaskAction,
    AgentFinishAction,
    AgentRecallAction,
    AgentSummarizeAction,
    AgentThinkAction,
    BrowseURLAction,
    CmdKillAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    ModifyTaskAction,
    NullAction,
    action_from_dict,
)
from opendevin.events.observation import (
    NullObservation,
    Observation,
)

ACTION_TYPE_TO_CLASS: Dict[str, Type[Action]] = {
    ActionType.RUN: CmdRunAction,
    ActionType.KILL: CmdKillAction,
    ActionType.BROWSE: BrowseURLAction,
    ActionType.READ: FileReadAction,
    ActionType.WRITE: FileWriteAction,
    ActionType.RECALL: AgentRecallAction,
    ActionType.THINK: AgentThinkAction,
    ActionType.SUMMARIZE: AgentSummarizeAction,
    ActionType.FINISH: AgentFinishAction,
    ActionType.ADD_TASK: AddTaskAction,
    ActionType.MODIFY_TASK: ModifyTaskAction,
}

HISTORY_SIZE = 10

prompt = """
# Task
You're a diligent software engineer AI. You can't see, draw, or interact with a
browser, but you can read and write files, and you can run commands, and you can think.

You've been given the following task:

%(task)s

## Plan
As you complete this task, you're building a plan and keeping
track of your progress. Here's a JSON representation of your plan:

%(plan)s


%(plan_status)s

You're responsible for managing this plan and the status of tasks in
it, by using the `add_task` and `modify_task` actions described below.

If the History below contradicts the state of any of these tasks, you
MUST modify the task using the `modify_task` action described below.

Be sure NOT to duplicate any tasks. Do NOT use the `add_task` action for
a task that's already represented. Every task must be represented only once.

Tasks that are sequential MUST be siblings. They must be added in order
to their parent task.

If you mark a task as 'completed', 'verified', or 'abandoned',
all non-abandoned subtasks will be marked the same way.
So before closing a task this way, you MUST not only be sure that it has
been completed successfully--you must ALSO be sure that all its subtasks
are ready to be marked the same way.

If, and only if, ALL tasks have already been marked verified,
you MUST respond with the `finish` action.

## History
Here is a recent history of actions you've taken in service of this plan,
as well as observations you've made. This only includes the MOST RECENT
ten actions--more happened before that.

%(history)s


Your most recent action is at the bottom of that history.

## Action
What is your next thought or action? Your response must be in JSON format.

It must be an object, and it must contain two fields:
* `action`, which is one of the actions below
* `args`, which is a map of key-value pairs, specifying the arguments for that action

* `read` - reads the content of a file. Arguments:
  * `path` - the path of the file to read
* `write` - writes the content to a file. Arguments:
  * `path` - the path of the file to write
  * `content` - the content to write to the file
* `run` - runs a command on the command line in a Linux shell. Arguments:
  * `command` - the command to run
  * `background` - if true, run the command in the background, so that other commands can be run concurrently. Useful for e.g. starting a server. You won't be able to see the logs. You don't need to end the command with `&`, just set this to true.
* `kill` - kills a background command
  * `id` - the ID of the background command to kill
* `browse` - opens a web page. Arguments:
  * `url` - the URL to open
* `think` - make a plan, set a goal, or record your thoughts. Arguments:
  * `thought` - the thought to record
* `add_task` - add a task to your plan. Arguments:
  * `parent` - the ID of the parent task
  * `goal` - the goal of the task
  * `subtasks` - a list of subtasks, each of which is a map with a `goal` key.
* `modify_task` - close a task. Arguments:
  * `id` - the ID of the task to close
  * `state` - set to 'in_progress' to start the task, 'completed' to finish it, 'verified' to assert that it was successful, 'abandoned' to give up on it permanently, or `open` to stop working on it for now.
* `finish` - if ALL of your tasks and subtasks have been verified or abandoned, and you're absolutely certain that you've completed your task and have tested your work, use the finish action to stop working.

You MUST take time to think in between read, write, run, browse, and recall actions.
You should never act twice in a row without thinking. But if your last several
actions are all `think` actions, you should consider taking a different action.

What is your next thought or action? Again, you must reply with JSON, and only with JSON.

%(hint)s
"""


def get_hint(latest_action_id: str) -> str:
    """Returns action type hint based on given action_id"""

    hints = {
        '': "You haven't taken any actions yet. Start by using `ls` to check out what files you're working with.",
        ActionType.RUN: 'You should think about the command you just ran, what output it gave, and how that affects your plan.',
        ActionType.READ: 'You should think about the file you just read, what you learned from it, and how that affects your plan.',
        ActionType.WRITE: 'You just changed a file. You should think about how it affects your plan.',
        ActionType.BROWSE: 'You should think about the page you just visited, and what you learned from it.',
        ActionType.THINK: "Look at your last thought in the history above. What does it suggest? Don't think anymore--take action.",
        ActionType.RECALL: 'You should think about the information you just recalled, and how it should affect your plan.',
        ActionType.ADD_TASK: 'You should think about the next action to take.',
        ActionType.MODIFY_TASK: 'You should think about the next action to take.',
        ActionType.SUMMARIZE: '',
        ActionType.FINISH: '',
    }
    return hints.get(latest_action_id, '')


def get_prompt(plan: Plan, history: List[Tuple[Action, Observation]]) -> str:
    """
    Gets the prompt for the planner agent.
    Formatted with the most recent action-observation pairs, current task, and hint based on last action

    Parameters:
    - plan (Plan): The original plan outlined by the user with LLM defined tasks
    - history (List[Tuple[Action, Observation]]): List of corresponding action-observation pairs

    Returns:
    - str: The formatted string prompt with historical values
    """

    plan_str = json.dumps(plan.task.to_dict(), indent=2)
    sub_history = history[-HISTORY_SIZE:]
    history_dicts = []
    latest_action: Action = NullAction()
    for action, observation in sub_history:
        if not isinstance(action, NullAction):
            history_dicts.append(action.to_memory())
            latest_action = action
        if not isinstance(observation, NullObservation):
            observation_dict = observation.to_memory()
            history_dicts.append(observation_dict)
    history_str = json.dumps(history_dicts, indent=2)
    current_task = plan.get_current_task()
    if current_task is not None:
        plan_status = f"You're currently working on this task:\n{current_task.goal}."
        if len(current_task.subtasks) == 0:
            plan_status += "\nIf it's not achievable AND verifiable with a SINGLE action, you MUST break it down into subtasks NOW."
    else:
        plan_status = "You're not currently working on any tasks. Your next action MUST be to mark a task as in_progress."
    hint = get_hint(latest_action.to_dict()['action'])
    logger.info('HINT:\n' + hint, extra={'msg_type': 'INFO'})
    return prompt % {
        'task': plan.main_goal,
        'plan': plan_str,
        'history': history_str,
        'hint': hint,
        'plan_status': plan_status,
    }


def parse_response(response: str) -> Action:
    """
    Parses the model output to find a valid action to take

    Parameters:
    - response (str): A response from the model that potentially contains an Action.

    Returns:
    - Action: A valid next action to perform from model output
    """
    json_start = response.find('{')
    json_end = response.rfind('}') + 1
    response = response[json_start:json_end]
    action_dict = json.loads(response)
    if 'contents' in action_dict:
        # The LLM gets confused here. Might as well be robust
        action_dict['content'] = action_dict.pop('contents')
    action = action_from_dict(action_dict)
    return action
