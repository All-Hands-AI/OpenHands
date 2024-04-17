import asyncio
import time
from typing import List, Callable
from opendevin.plan import Plan
from opendevin.state import State
from opendevin.agent import Agent
from opendevin.observation import Observation, AgentErrorObservation, NullObservation
from litellm.exceptions import APIConnectionError
from openai import AuthenticationError

from opendevin import config
from opendevin.logger import opendevin_logger as logger

from opendevin.exceptions import MaxCharsExceedError
from .action_manager import ActionManager

from opendevin.action import (
    Action,
    NullAction,
    AgentFinishAction,
)
from opendevin.exceptions import AgentNoActionError

MAX_ITERATIONS = config.get('MAX_ITERATIONS')
MAX_CHARS = config.get('MAX_CHARS')


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    action_manager: ActionManager
    callbacks: List[Callable]

    def __init__(
        self,
        agent: Agent,
        sid: str = '',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        container_image: str | None = None,
        callbacks: List[Callable] = [],
    ):
        self.id = sid
        self.agent = agent
        self.max_iterations = max_iterations
        self.action_manager = ActionManager(self.id, container_image)
        self.max_chars = max_chars
        self.callbacks = callbacks

    def update_state_for_step(self, i):
        self.state.iteration = i
        self.state.background_commands_obs = self.action_manager.get_background_obs()

    def update_state_after_step(self):
        self.state.updated_info = []

    def add_history(self, action: Action, observation: Observation):
        if not isinstance(action, Action):
            raise TypeError(
                f'action must be an instance of Action, got {type(action).__name__} instead')
        if not isinstance(observation, Observation):
            raise TypeError(
                f'observation must be an instance of Observation, got {type(observation).__name__} instead')
        self.state.history.append((action, observation))
        self.state.updated_info.append((action, observation))

    async def start_loop(self, task: str):
        finished = False
        plan = Plan(task)
        self.state = State(plan)
        for i in range(self.max_iterations):
            try:
                finished = await self.step(i)
            except Exception as e:
                logger.error('Error in loop', exc_info=True)
                raise e
            if finished:
                break
        if not finished:
            logger.info('Exited before finishing the task.')

    async def step(self, i: int):
        logger.info(f'STEP {i}', extra={'msg_type': 'STEP'})
        logger.info(self.state.plan.main_goal, extra={'msg_type': 'PLAN'})
        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(
                self.state.num_of_chars, self.max_chars)

        log_obs = self.action_manager.get_background_obs()
        for obs in log_obs:
            self.add_history(NullAction(), obs)
            await self._run_callbacks(obs)
            logger.info(obs, extra={'msg_type': 'BACKGROUND LOG'})

        self.update_state_for_step(i)
        action: Action = NullAction()
        observation: Observation = NullObservation('')
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise AgentNoActionError()
            logger.info(action, extra={'msg_type': 'ACTION'})
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            logger.error(e)

            if isinstance(e, APIConnectionError):
                time.sleep(3)

            # raise specific exceptions that need to be handled outside
            # note: we are using AuthenticationError class from openai rather than
            # litellm because:
            # 1) litellm.exceptions.AuthenticationError is a subclass of openai.AuthenticationError
            # 2) embeddings call, initiated by llama-index, has no wrapper for authentication
            #    errors. This means we have to catch individual authentication errors
            #    from different providers, and OpenAI is one of these.
            if isinstance(e, (AuthenticationError, AgentNoActionError)):
                raise
        self.update_state_after_step()

        await self._run_callbacks(action)

        finished = isinstance(action, AgentFinishAction)
        if finished:
            logger.info(action, extra={'msg_type': 'INFO'})
            return True

        if isinstance(observation, NullObservation):
            observation = await self.action_manager.run_action(action, self)

        if not isinstance(observation, NullObservation):
            logger.info(observation, extra={'msg_type': 'OBSERVATION'})

        self.add_history(action, observation)
        await self._run_callbacks(observation)

    async def _run_callbacks(self, event):
        if event is None:
            return
        for callback in self.callbacks:
            idx = self.callbacks.index(callback)
            try:
                callback(event)
            except Exception as e:
                logger.exception(f'Callback error: {e}, idx: {idx}')
        await asyncio.sleep(
            0.001
        )  # Give back control for a tick, so we can await in callbacks
