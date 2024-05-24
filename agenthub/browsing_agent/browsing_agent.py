import ast

from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.utils.obs import flatten_axtree_to_str

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentFinishAction,
    BrowseInteractiveAction,
    MessageAction,
)
from opendevin.events.observation import BrowserOutputObservation
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins import (
    PluginRequirement,
)


def parse_response(response: str) -> Action:
    if '```' not in response:
        # unexpected response format, message back to user
        return MessageAction(response)
    thought = response.split('```')[0].strip()
    action_str = response.split('```')[1].strip()
    # handle send message to user function call in BrowserGym
    for sub_action in action_str.split('\n'):
        if 'send_msg_to_user(' in sub_action:
            tree = ast.parse(sub_action)
            args = tree.body[0].value.args  # type: ignore
            return MessageAction(args[0].value)

    return BrowseInteractiveAction(browser_actions=action_str, thought=thought)


class BrowsingAgent(Agent):
    VERSION = '1.0'
    """
    An agent that interacts with the browser.
    """

    sandbox_plugins: list[PluginRequirement] = []

    def __init__(
        self,
        llm: LLM,
    ) -> None:
        """
        Initializes a new instance of the BrowsingAgent class.

        Parameters:
        - llm (LLM): The llm to be used by this agent
        """
        super().__init__(llm)
        self.action_space = HighLevelActionSet(
            # see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/highlevel.py for more details
            subsets=[
                'chat',
                'bid',
                'nav',
            ],  # define a configurable action space, with chat functionality, web navigation, and webpage grounding using accessibility tree and HTML.
            strict=False,  # less strict on the parsing of the actions
            multiaction=True,  # enable to agent to take multiple actions at once
        )

        self.reset()

    def reset(self) -> None:
        """
        Resets the Browsing Agent.
        """
        super().reset()
        self.cost_accumulator = 0

    def step(self, state: State) -> Action:
        """
        Performs one step using the Browsing Agent.
        This includes gathering information on previous steps and prompting the model to make a browsing command to execute.

        Parameters:
        - state (State): used to get updated info

        Returns:
        - BrowseInteractiveAction(browsergym_command) - BrowserGym commands to run
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """
        goal = state.get_current_user_intent()
        messages = []
        prev_actions = ''
        cur_axtree_txt = ''
        error_prefix = ''
        last_obs = None
        for prev_action, obs in state.history:
            if isinstance(prev_action, BrowseInteractiveAction):
                prev_actions += f'{prev_action.browser_actions}\n'
                last_obs = obs
            elif (
                isinstance(prev_action, MessageAction) and prev_action.source != 'user'
            ):
                # agent has responded, task finish.
                return AgentFinishAction()

        if isinstance(last_obs, BrowserOutputObservation):
            if last_obs.error:
                # add error recovery prompt prefix
                error_prefix = f'IMPORTANT! Last action is incorrect:\n{last_obs.last_browser_action}\nThink again with the current observation of the page.\n'
            cur_axtree_txt = flatten_axtree_to_str(last_obs.axtree_object)

        system_msg = f"""\
# Instructions
Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

# Goal:
{goal}

# Action Space
{self.action_space.describe(with_long_description=False, with_examples=True)}
"""

        messages.append({'role': 'system', 'content': system_msg})

        prompt = f"""\
{error_prefix}

# Current Accessibility Tree:
{cur_axtree_txt}

# Previous Actions
{prev_actions}

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click("12")```
"
""".strip()
        messages.append({'role': 'user', 'content': prompt})
        response = self.llm.completion(
            messages=messages,
            temperature=0.0,
        )
        self.log_cost(response)
        action_resp = response['choices'][0]['message']['content']
        logger.info(prompt)
        logger.info(action_resp)
        return parse_response(action_resp)

    def search_memory(self, query: str) -> list[str]:
        raise NotImplementedError('Implement this abstract method')

    def log_cost(self, response):
        # TODO: refactor to unified cost tracking
        try:
            cur_cost = self.llm.completion_cost(response)
        except Exception:
            cur_cost = 0
        self.cost_accumulator += cur_cost
        logger.info(
            'Cost: %.2f USD | Accumulated Cost: %.2f USD',
            cur_cost,
            self.cost_accumulator,
        )
