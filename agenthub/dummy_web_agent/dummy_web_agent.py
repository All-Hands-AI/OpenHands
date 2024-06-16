import os
import time
from typing import Any, Dict, List, Optional

from browsergym.core.action.highlevel import HighLevelActionSet

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentFinishAction,
    BrowseInteractiveAction,
    MessageAction,
)
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins import (
    PluginRequirement,
)
from opendevin.runtime.tools import RuntimeTool

USE_NAV = (
    os.environ.get('USE_NAV', 'true') == 'true'
)  # only disable NAV actions when running webarena and miniwob benchmarks
USE_CONCISE_ANSWER = (
    os.environ.get('USE_CONCISE_ANSWER', 'false') == 'true'
)  # only return concise answer when running webarena and miniwob benchmarks

if not USE_NAV and USE_CONCISE_ANSWER:
    EVAL_MODE = True  # disabled NAV actions and only return concise answer, for webarena and miniwob benchmarks\
else:
    EVAL_MODE = False


class ParseError(Exception):
    pass


class DummyWebAgent(Agent):
    VERSION = '1.0'
    """
    An agent that interacts with the browser.
    """

    sandbox_plugins: list[PluginRequirement] = []
    runtime_tools: list[RuntimeTool] = [RuntimeTool.BROWSER]

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
        # define a configurable action space, with chat functionality, web navigation, and webpage grounding using accessibility tree and HTML.
        # see https://github.com/ServiceNow/BrowserGym/blob/main/core/src/browsergym/core/action/highlevel.py for more details
        action_subsets = ['chat', 'bid']
        if USE_NAV:
            action_subsets.append('nav')
        self.action_space = HighLevelActionSet(
            subsets=action_subsets,
            strict=False,  # less strict on the parsing of the actions
            multiaction=False,  # enable to agent to take multiple actions at once
        )
        self.temperature = 0.0
        self.max_retry = 4

        self.reset()

    def reset(self) -> None:
        """
        Resets the Browsing Agent.
        """
        super().reset()
        self.cost_accumulator = 0
        self.error_accumulator = 0

        self.actions: List[str] = []
        self.obs_history: List[Dict[str, Any]] = []
        self.states: List[str] = []
        self.evaluations: List[str] = []
        self.strategies: List[Optional[str]] = []
        self.active_strategy: Optional[str] = None

    def step(self, env_state: State) -> Action:
        """
        Performs one step using the Browsing Agent.
        This includes gathering information on previous steps and prompting the model to make a browsing command to execute.

        Parameters:
        - env_state (State): used to get updated info

        Returns:
        - BrowseInteractiveAction(browsergym_command) - BrowserGym commands to run
        - MessageAction(content) - Message action to run (e.g. ask for clarification)
        - AgentFinishAction() - end the interaction
        """

        time.sleep(3)
        self.actions.append('foo')
        if len(self.actions) == 1:
            return MessageAction('test')
        elif len(self.actions) == 2:
            return BrowseInteractiveAction(
                browser_actions="goto('https://www.google.com')",
                thought='# Header\n\nText',
            )
        elif len(self.actions) < 4:
            return BrowseInteractiveAction(
                browser_actions='noop()', thought='# Header\n\nText'
            )
        elif len(self.actions) == 4:
            return MessageAction('test 2')
        else:
            return AgentFinishAction(outputs={'content': 'None'})

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
