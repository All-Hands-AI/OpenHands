import asyncio
import traceback
from typing import Callable, List, Type

from openai import AuthenticationError, APIConnectionError
from litellm import ContextWindowExceededError

from opendevin import config
from opendevin.action import (
    Action,
    AgentFinishAction,
    AgentDelegateAction,
    NullAction,
)
from opendevin.observation import (
    Observation,
    AgentErrorObservation,
    AgentDelegateObservation,
    NullObservation,
)
from opendevin.agent import Agent
from opendevin.exceptions import AgentNoActionError, MaxCharsExceedError
from opendevin.logger import opendevin_logger as logger
from opendevin.plan import Plan
from opendevin.state import State

from ..action.tasks import TaskStateChangedAction
from ..schema import TaskState
from .action_manager import ActionManager

MAX_ITERATIONS = config.get('MAX_ITERATIONS')
MAX_CHARS = config.get('MAX_CHARS')


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    action_manager: ActionManager
    callbacks: List[Callable]

    delegate: 'AgentController | None' = None
    state: State | None = None

    _task_state: TaskState = TaskState.INIT
    _cur_step: int = 0

    def __init__(
        self,
        agent: Agent,
        sid: str = 'default',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        callbacks: List[Callable] = [],
    ):
        self.id = sid
        self.agent = agent
        self.max_iterations = max_iterations
        self.action_manager = ActionManager(self.id)
        self.max_chars = max_chars
        self.callbacks = callbacks

    def update_state_for_step(self, i):
        if self.state is None:
            return
        self.state.iteration = i
        self.state.background_commands_obs = self.action_manager.get_background_obs()

    def update_state_after_step(self):
        if self.state is None:
            return
        self.state.updated_info = []

    def add_history(self, action: Action, observation: Observation):
        if self.state is None:
            return
        if not isinstance(action, Action):
            raise TypeError(
                f'action must be an instance of Action, got {type(action).__name__} instead'
            )
        if not isinstance(observation, Observation):
            raise TypeError(
                f'observation must be an instance of Observation, got {type(observation).__name__} instead'
            )
        self.state.history.append((action, observation))
        self.state.updated_info.append((action, observation))

    async def _run(self):
        if self.state is None:
            return

        if self._task_state != TaskState.RUNNING:
            raise ValueError('Task is not in running state')

        for i in range(self._cur_step, self.max_iterations):
            self._cur_step = i
            try:
                finished = await self.step(i)
                if finished:
                    self._task_state = TaskState.FINISHED
            except Exception as e:
                logger.error('Error in loop', exc_info=True)
                raise e

            if self._task_state == TaskState.FINISHED:
                logger.info('Task finished by agent')
                await self.reset_task()
                break
            elif self._task_state == TaskState.STOPPED:
                logger.info('Task stopped by user')
                await self.reset_task()
                break
            elif self._task_state == TaskState.PAUSED:
                logger.info('Task paused')
                self._cur_step = i + 1
                await self.notify_task_state_changed()
                break

    async def setup_task(self, task: str):
        self._task_state = TaskState.RUNNING
        await self.notify_task_state_changed()
        self.state = State(Plan(task))

    async def start(self, task: str):
        """Starts the agent controller with a task.
        If task already run before, it will continue from the last step.
        """
        await self.setup_task(task)
        await self._run()

    async def resume(self):
        if self.state is None:
            raise ValueError('No task to resume')

        self._task_state = TaskState.RUNNING
        await self.notify_task_state_changed()

        await self._run()

    async def reset_task(self):
        self.state = None
        self._cur_step = 0
        self._task_state = TaskState.INIT
        self.agent.reset()
        await self.notify_task_state_changed()

    async def set_task_state_to(self, state: TaskState):
        self._task_state = state
        if state == TaskState.STOPPED:
            await self.reset_task()
        logger.info(f'Task state set to {state}')

    def get_task_state(self):
        """Returns the current state of the agent task."""
        return self._task_state

    async def notify_task_state_changed(self):
        await self._run_callbacks(TaskStateChangedAction(self._task_state))

    async def start_delegate(self, action: AgentDelegateAction):
        AgentCls: Type[Agent] = Agent.get_cls(action.agent)
        agent = AgentCls(llm=self.agent.llm)
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=agent,
            max_iterations=self.max_iterations,
            max_chars=self.max_chars,
            callbacks=self.callbacks,
        )
        task = action.inputs.get('task') or ''
        await self.delegate.setup_task(task)

    async def step(self, i: int) -> bool:
        if self.state is None:
            raise ValueError('No task to run')
        if self.delegate is not None:
            delegate_done = await self.delegate.step(i)
            if delegate_done:
                result = self.delegate.state.results if self.delegate.state else {}
                obs: Observation = AgentDelegateObservation(content='', outputs=result)
                self.add_history(NullAction(), obs)
                self.delegate = None
                self.delegateAction = None
            return False

        logger.info(f'STEP {i}', extra={'msg_type': 'STEP'})
        logger.info(self.state.plan.main_goal, extra={'msg_type': 'PLAN'})
        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(self.state.num_of_chars, self.max_chars)

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
            logger.debug(traceback.format_exc())

            # raise specific exceptions that need to be handled outside
            # note: we are using classes from openai rather than litellm because:
            # 1) litellm.exceptions.AuthenticationError is a subclass of openai.AuthenticationError
            # 2) embeddings call, initiated by llama-index, has no wrapper for errors.
            #    This means we have to catch individual authentication errors
            #    from different providers, and OpenAI is one of these.
            if isinstance(e, (AuthenticationError, ContextWindowExceededError, APIConnectionError)):
                raise

        self.update_state_after_step()

        await self._run_callbacks(action)

        finished = isinstance(action, AgentFinishAction)
        if finished:
            self.state.result = action.outputs  # type: ignore[attr-defined]
            logger.info(action, extra={'msg_type': 'INFO'})
            return True

        if isinstance(observation, NullObservation):
            observation = await self.action_manager.run_action(action, self)

        if not isinstance(observation, NullObservation):
            logger.info(observation, extra={'msg_type': 'OBSERVATION'})

        self.add_history(action, observation)
        await self._run_callbacks(observation)
        return False

    async def _run_callbacks(self, event):
        if event is None:
            return
        for callback in self.callbacks:
            idx = self.callbacks.index(callback)
            try:
                await callback(event)
            except Exception as e:
                logger.exception(f'Callback error: {e}, idx: {idx}')
        await asyncio.sleep(
            0.001
        )  # Give back control for a tick, so we can await in callbacks

    def get_state(self):
        return self.state
