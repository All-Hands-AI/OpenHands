import asyncio
from typing import Callable, List, Optional, Type

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.controller.action_manager import ActionManager
from opendevin.controller.agent import Agent
from opendevin.controller.state.plan import Plan
from opendevin.controller.state.state import State
from opendevin.core import config
from opendevin.core.exceptions import (
    AgentMalformedActionError,
    AgentNoActionError,
    LLMOutputError,
    MaxCharsExceedError,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import TaskState
from opendevin.core.schema.config import ConfigType
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentTalkAction,
    NullAction,
    TaskStateChangedAction,
)
from opendevin.events.observation import (
    AgentDelegateObservation,
    AgentErrorObservation,
    NullObservation,
    Observation,
    UserMessageObservation,
)
from opendevin.runtime import DockerSSHBox, Sandbox
from opendevin.runtime.browser.browser_env import BrowserEnv

MAX_ITERATIONS = config.get(ConfigType.MAX_ITERATIONS)
MAX_CHARS = config.get(ConfigType.MAX_CHARS)


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    action_manager: ActionManager
    callbacks: List[Callable]
    browser: BrowserEnv

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
        fake_user_response_fn: Optional[Callable[[Optional[State]], str]] = None,
        sandbox: Optional[Sandbox] = None,
    ):
        """Initializes a new instance of the AgentController class.

        Args:
            agent: The agent instance to control.
            sid: The session ID of the agent.
            max_iterations: The maximum number of iterations the agent can run.
            max_chars: The maximum number of characters the agent can output.
            callbacks: A list of callback functions to run after each action.
            fake_user_response_fn: A optional function that receives the current state (could be None) and returns a fake user response.
            sandbox: An optional initialized sandbox to run the agent in. If not provided, a default sandbox will be created based on config.
        """
        self.id = sid
        self.agent = agent
        self.max_iterations = max_iterations
        self.action_manager = ActionManager(self.id, sandbox=sandbox)
        self.max_chars = max_chars
        self.callbacks = callbacks
        self.fake_user_response_fn = fake_user_response_fn
        # Initialize agent-required plugins for sandbox (if any)
        self.action_manager.init_sandbox_plugins(agent.sandbox_plugins)
        # Initialize browser environment
        self.browser = BrowserEnv()

        if isinstance(agent, CodeActAgent) and not isinstance(
            self.action_manager.sandbox, DockerSSHBox
        ):
            logger.warning(
                'CodeActAgent requires DockerSSHBox as sandbox! Using other sandbox that are not stateful (LocalBox, DockerExecBox) will not work properly.'
            )

        self._await_user_message_queue: asyncio.Queue = asyncio.Queue()

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

    async def _run(self) -> Optional[State]:
        if self.state is None:
            return None

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
                    AgentErrorObservation(
                        'Oops! Something went wrong while completing your task. You can check the logs for more info.'
                    )
                )
                await self.set_task_state_to(TaskState.STOPPED)
                break

            if self._task_state == TaskState.FINISHED:
                logger.info('Task finished by agent')
                finished_state = self.state
                await self.reset_task()
                return finished_state
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
                observation = AgentErrorObservation(
                    'I got stuck into a loop, the task has stopped.'
                )
                await self._run_callbacks(observation)
                await self.set_task_state_to(TaskState.STOPPED)
                break
        return self.state

    async def setup_task(self, task: str, inputs: dict = {}):
        """Sets up the agent controller with a task."""
        self._task_state = TaskState.RUNNING
        await self.notify_task_state_changed()
        self.state = State(Plan(task))
        self.state.inputs = inputs

    async def start(self, task: str) -> Optional[State]:
        """Starts the agent controller with a task.
        If task already run before, it will continue from the last step.
        """
        await self.setup_task(task)
        finished_state = await self._run()
        return finished_state

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

    async def add_user_message(self, message: UserMessageObservation):
        if self.state is None:
            return

        if self._task_state == TaskState.AWAITING_USER_INPUT:
            self._await_user_message_queue.put_nowait(message)

            # set the task state to running
            self._task_state = TaskState.RUNNING
            await self.notify_task_state_changed()

        elif self._task_state == TaskState.RUNNING:
            self.add_history(NullAction(), message)

        else:
            raise ValueError(
                f'Task (state: {self._task_state}) is not in a state to add user message'
            )

    async def wait_for_user_input(self) -> UserMessageObservation:
        self._task_state = TaskState.AWAITING_USER_INPUT
        await self.notify_task_state_changed()
        # wait for the next user message
        if self.fake_user_response_fn:
            message = self.fake_user_response_fn(self.state)
            user_message_observation = UserMessageObservation(message)
        elif len(self.callbacks) == 0:
            logger.info(
                'Use STDIN to request user message as no callbacks are registered',
                extra={'msg_type': 'INFO'},
            )
            message = input('Request user input [type /exit to stop interaction] >> ')
            user_message_observation = UserMessageObservation(message)
        else:
            user_message_observation = await self._await_user_message_queue.get()
            self._await_user_message_queue.task_done()
        return user_message_observation

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
        if i == 0:
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
                raise AgentNoActionError('No action was returned')
        except (AgentMalformedActionError, AgentNoActionError, LLMOutputError) as e:
            observation = AgentErrorObservation(str(e))
        logger.info(action, extra={'msg_type': 'ACTION'})

        self.update_state_after_step()

        await self._run_callbacks(action)

        # whether to await for user messages
        if isinstance(action, AgentTalkAction):
            # await for the next user messages
            user_message_observation = await self.wait_for_user_input()
            logger.info(user_message_observation, extra={'msg_type': 'OBSERVATION'})
            self.add_history(action, user_message_observation)
            return False

        finished = isinstance(action, AgentFinishAction)
        if finished:
            self.state.outputs = action.outputs  # type: ignore[attr-defined]
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

    def _is_stuck(self):
        if (
            self.state is None
            or self.state.history is None
            or len(self.state.history) < 3
        ):
            return False

        # if the last three (Action, Observation) tuples are too repetitive
        # the agent got stuck in a loop
        if all(
            [
                self.state.history[-i][0] == self.state.history[-3][0]
                for i in range(1, 3)
            ]
        ):
            # it repeats same action, give it a chance, but not if:
            if all(
                isinstance(self.state.history[-i][1], NullObservation)
                for i in range(1, 4)
            ):
                # same (Action, NullObservation): like 'think' the same thought over and over
                logger.debug('Action, NullObservation loop detected')
                return True
            elif all(
                isinstance(self.state.history[-i][1], AgentErrorObservation)
                for i in range(1, 4)
            ):
                # (NullAction, AgentErrorObservation): errors coming from an exception
                # (Action, AgentErrorObservation): the same action getting an error, even if not necessarily the same error
                logger.debug('Action, AgentErrorObservation loop detected')
                return True

        return False
