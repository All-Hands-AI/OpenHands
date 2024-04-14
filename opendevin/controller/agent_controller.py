import asyncio
import inspect
import traceback
import time
from typing import List, Callable, Literal, Mapping, Awaitable, Any, cast

from termcolor import colored
from litellm.exceptions import APIConnectionError
from openai import AuthenticationError

from opendevin import config
from opendevin.action import (
    Action,
    NullAction,
    AgentFinishAction,
    AddTaskAction,
    ModifyTaskAction,
)
from opendevin.agent import Agent
from opendevin.logger import opendevin_logger as logger
from opendevin.exceptions import MaxCharsExceedError, AgentNoActionError
from opendevin.observation import Observation, AgentErrorObservation, NullObservation
from opendevin.plan import Plan
from opendevin.state import State
from .command_manager import CommandManager

ColorType = Literal[
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'light_grey',
    'dark_grey',
    'light_red',
    'light_green',
    'light_yellow',
    'light_blue',
    'light_magenta',
    'light_cyan',
    'white',
]

DISABLE_COLOR_PRINTING = (
    config.get('DISABLE_COLOR').lower() == 'true'
)
MAX_ITERATIONS = config.get('MAX_ITERATIONS')
MAX_CHARS = config.get('MAX_CHARS')


def print_with_color(text: Any, print_type: str = 'INFO'):
    TYPE_TO_COLOR: Mapping[str, ColorType] = {
        'BACKGROUND LOG': 'blue',
        'ACTION': 'green',
        'OBSERVATION': 'yellow',
        'INFO': 'cyan',
        'ERROR': 'red',
        'PLAN': 'light_magenta',
    }
    color = TYPE_TO_COLOR.get(print_type.upper(), TYPE_TO_COLOR['INFO'])
    if DISABLE_COLOR_PRINTING:
        print(f'\n{print_type.upper()}:\n{str(text)}', flush=True)
    else:
        print(
            colored(f'\n{print_type.upper()}:\n', color, attrs=['bold'])
            + colored(str(text), color),
            flush=True,
        )


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    command_manager: CommandManager
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
        self.command_manager = CommandManager(self.id, container_image)
        self.max_chars = max_chars
        self.callbacks = callbacks

    def update_state_for_step(self, i):
        self.state.iteration = i
        self.state.background_commands_obs = self.command_manager.get_background_obs()

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
        print('\n\n==============', flush=True)
        print('STEP', i, flush=True)
        print_with_color(self.state.plan.main_goal, 'PLAN')
        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(
                self.state.num_of_chars, self.max_chars)

        log_obs = self.command_manager.get_background_obs()
        for obs in log_obs:
            self.add_history(NullAction(), obs)
            await self._run_callbacks(obs)
            print_with_color(obs, 'BACKGROUND LOG')

        self.update_state_for_step(i)
        action: Action = NullAction()
        observation: Observation = NullObservation('')
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise AgentNoActionError()
            print_with_color(action, 'ACTION')
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            print_with_color(observation, 'ERROR')
            traceback.print_exc()
            if isinstance(e, APIConnectionError):
                time.sleep(3)
            # TODO Change to more robust error handling
            if (
                'The api_key client option must be set' in observation.content
                or 'Incorrect API key provided:' in observation.content
            ):
                raise

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
            print_with_color(action, 'INFO')
            return True

        if isinstance(action, AddTaskAction):
            try:
                self.state.plan.add_subtask(
                    action.parent, action.goal, action.subtasks)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, 'ERROR')
                traceback.print_exc()
        elif isinstance(action, ModifyTaskAction):
            try:
                self.state.plan.set_subtask_state(action.id, action.state)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, 'ERROR')
                traceback.print_exc()

        if action.executable:
            try:
                if inspect.isawaitable(action.run(self)):
                    observation = await cast(Awaitable[Observation], action.run(self))
                else:
                    observation = action.run(self)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, 'ERROR')
                traceback.print_exc()

        if not isinstance(observation, NullObservation):
            print_with_color(observation, 'OBSERVATION')

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
