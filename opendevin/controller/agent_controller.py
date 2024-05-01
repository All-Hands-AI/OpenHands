import asyncio
from typing import Callable, List, Type

from opendevin import config
from opendevin.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    NullAction,
)
from opendevin.action.tasks import TaskStateChangedAction
from opendevin.agent import Agent
from opendevin.controller.action_manager import ActionManager
from opendevin.exceptions import (
    AgentMalformedActionError,
    AgentNoActionError,
    LLMOutputError,
    MaxCharsExceedError,
)
from opendevin.logger import opendevin_logger as logger
from opendevin.observation import (
    AgentDelegateObservation,
    AgentErrorObservation,
    NullObservation,
    Observation,
)
from opendevin.plan import Plan
from opendevin.schema import TaskState
from opendevin.schema.config import ConfigType
from opendevin.state import State

MAX_ITERATIONS = config.get(ConfigType.MAX_ITERATIONS)
MAX_CHARS = config.get(ConfigType.MAX_CHARS)


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

    delegate: 'AgentController | None' = None
    state: State | None = None

    _task_state: TaskState = TaskState.INIT
    _cur_step: int = 0

    def __init__(
        self,
        agent: Agent,
        inputs: dict = {},
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
        # Initialize agent-required plugins for sandbox (if any)
        self.action_manager.init_sandbox_plugins(agent.sandbox_plugins)

    def update_state_for_step(self, i):
        if self.state is None:
            return
        self.state.iteration = i
        self.state.background_commands_obs = self.command_manager.get_background_obs()

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
            except Exception:
                logger.error('Error in loop', exc_info=True)
                await self._run_callbacks(
                    AgentErrorObservation('Oops! Something went wrong while completing your task. You can check the logs for more info.'))
                await self.set_task_state_to(TaskState.STOPPED)
                break

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

            if self._is_stuck():
                logger.info('Loop detected, stopping task')
                observation = AgentErrorObservation('I got stuck into a loop, the task has stopped.')
                await self._run_callbacks(observation)
                await self.set_task_state_to(TaskState.STOPPED)
                break

    async def setup_task(self, task: str, inputs: dict = {}):
        """Sets up the agent controller with a task.
        """
        self._task_state = TaskState.RUNNING
        await self.notify_task_state_changed()
        self.state = State(Plan(task))
        self.state.inputs = inputs

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
        await self.delegate.setup_task(task, action.inputs)

    async def step(self, i: int) -> bool:
        if self.state is None:
            raise ValueError('No task to run')
        if self.delegate is not None:
            delegate_done = await self.delegate.step(i)
            if delegate_done:
                outputs = self.delegate.state.outputs if self.delegate.state else {}
                obs: Observation = AgentDelegateObservation(content='', outputs=outputs)
                self.add_history(NullAction(), obs)
                self.delegate = None
                self.delegateAction = None
            return False

        logger.info(f'STEP {i}', extra={'msg_type': 'STEP'})
        logger.info(self.state.plan.main_goal, extra={'msg_type': 'PLAN'})
        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(self.state.num_of_chars, self.max_chars)

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
                raise AgentNoActionError('No action was returned')
        except (AgentMalformedActionError, AgentNoActionError, LLMOutputError) as e:
            observation = AgentErrorObservation(str(e))
        logger.info(action, extra={'msg_type': 'ACTION'})

        self.update_state_after_step()

        await self._run_callbacks(action)

        finished = isinstance(action, AgentFinishAction)
        if finished:
            self.state.outputs = action.outputs  # type: ignore[attr-defined]
            logger.info(action, extra={'msg_type': 'INFO'})
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
                observation = action.run(self)
                if inspect.isawaitable(observation):
                    observation = await cast(Awaitable[Observation], observation)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, 'ERROR')
                traceback.print_exc()

        if not isinstance(observation, NullObservation):
            print_with_color(observation, 'OBSERVATION')

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

    def _is_stuck(self):
        if self.state is None or self.state.history is None or len(self.state.history) < 3:
            return False

        # if the last three (Action, Observation) tuples are too repetitive
        # the agent got stuck in a loop
        if all(
            [self.state.history[-i][0] == self.state.history[-3][0] for i in range(1, 3)]
        ):
            # it repeats same action, give it a chance, but not if:
            if (all
                    (isinstance(self.state.history[-i][1], NullObservation) for i in range(1, 4))):
                # same (Action, NullObservation): like 'think' the same thought over and over
                logger.debug('Action, NullObservation loop detected')
                return True
            elif (all
                  (isinstance(self.state.history[-i][1], AgentErrorObservation) for i in range(1, 4))):
                # (NullAction, AgentErrorObservation): errors coming from an exception
                # (Action, AgentErrorObservation): the same action getting an error, even if not necessarily the same error
                logger.debug('Action, AgentErrorObservation loop detected')
                return True

        return False
