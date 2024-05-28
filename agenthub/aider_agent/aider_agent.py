from typing import TypedDict

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
)
from opendevin.events.observation import (
    Observation,
)
from opendevin.llm.llm import LLM

ActionObs = TypedDict(
    'ActionObs', {'action': Action, 'observations': list[Observation]}
)


class AiderAgent(Agent):
    VERSION = '1.0'
    """
    This is an agent based on aider: https://aider.chat/
    """

    def __init__(self, llm: LLM):
        try:
            from aider.models import Model
        except ImportError:
            logger.error(
                'Please install aider with `pip install aider-chat` to use AiderAgent'
            )
            raise
        super().__init__(llm)
        self.model = Model(llm.model_name, weak_model=llm.model_name)

    def step(self, state: State) -> Action:
        try:
            from aider.coders import Coder
        except ImportError:
            logger.error(
                'Please install aider with `pip install aider-chat` to use AiderAgent'
            )
            raise
        self.coder = Coder.create(main_model=self.model, fnames=['./'])
        # We'll need to figure out how to pass in the history here
        raise NotImplementedError
