import asyncio
import inspect
import traceback
from typing import List, Callable, Awaitable, cast
from opendevin.plan import Plan
from opendevin.state import State
from opendevin.agent import Agent
from opendevin.observation import Observation, AgentErrorObservation, NullObservation
from opendevin import config
from opendevin.logger import opendevin_logger as logger

from opendevin.exceptions import MaxCharsExceedError
from .command_manager import CommandManager

from opendevin.action import (
    Action,
    NullAction,
    AgentFinishAction,
    AddTaskAction,
    ModifyTaskAction,
)


MAX_ITERATIONS = config.get('MAX_ITERATIONS')
MAX_CHARS = config.get('MAX_CHARS')


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    workdir: str
    command_manager: CommandManager
    callbacks: List[Callable]

    def __init__(
        self,
        agent: Agent,
        workdir: str,
        sid: str = '',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        container_image: str | None = None,
        callbacks: List[Callable] = [],
    ):
        self.id = sid
        self.agent = agent
        self.max_iterations = max_iterations
        self.max_chars = max_chars
        self.workdir = workdir
        self.command_manager = CommandManager(
            self.id, workdir, container_image)
        self.callbacks = callbacks

    def update_state_for_step(self, i):
        self.state.iteration = i
        self.state.background_commands_obs = self.command_manager.get_background_obs()

    def update_state_after_step(self):
        self.state.updated_info = []

    def add_history(self, action: Action, observation: Observation):
        if not isinstance(action, Action):
            raise ValueError('action must be an instance of Action')
        if not isinstance(observation, Observation):
            raise ValueError('observation must be an instance of Observation')
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
        logger.info('\n\n==============', extra={'msg_type': 'STEP'})
        logger.info(f'STEP {i}', extra={'msg_type': 'STEP'})
        logger.info(self.state.plan.main_goal, extra={'msg_type': 'PLAN'})

        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(
                self.state.num_of_chars, self.max_chars)

        log_obs = self.command_manager.get_background_obs()
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
                raise ValueError('Agent must return an action')
            logger.info(action, extra={'msg_type': 'ACTION'})
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            logger.info(observation, extra={'msg_type': 'ERROR'})
            traceback.print_exc()
            # TODO Change to more robust error handling
            if (
                'The api_key client option must be set' in observation.content
                or 'Incorrect API key provided:' in observation.content
            ):
                raise
        self.update_state_after_step()

        await self._run_callbacks(action)

        finished = isinstance(action, AgentFinishAction)
        if finished:
            logger.info(action, extra={'msg_type': 'INFO'})
            return True

        if isinstance(action, AddTaskAction):
            try:
                self.state.plan.add_subtask(
                    action.parent, action.goal, action.subtasks)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                logger.info(observation, extra={'msg_type': 'ERROR'})
                traceback.print_exc()
        elif isinstance(action, ModifyTaskAction):
            try:
                self.state.plan.set_subtask_state(action.id, action.state)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                logger.info(observation, extra={'msg_type': 'ERROR'})
                traceback.print_exc()

        if action.executable:
            try:
                if inspect.isawaitable(action.run(self)):
                    observation = await cast(Awaitable[Observation], action.run(self))
                else:
                    observation = action.run(self)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                logger.info(observation, extra={'msg_type': 'ERROR'})
                traceback.print_exc()

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
                logger.exception(f"Callback error: {e}, idx: {idx}")
        await asyncio.sleep(
            0.001
        )  # Give back control for a tick, so we can await in callbacks
