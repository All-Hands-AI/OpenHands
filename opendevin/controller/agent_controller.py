import asyncio
from typing import Type

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
from opendevin.core.schema import AgentState
from opendevin.core.schema.config import ConfigType
from opendevin.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    AgentTalkAction,
    ChangeAgentStateAction,
    NullAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    AgentDelegateObservation,
    AgentErrorObservation,
    AgentStateChangedObservation,
    NullObservation,
    Observation,
    UserMessageObservation,
)
from opendevin.events.stream import EventStream
from opendevin.runtime import DockerSSHBox
from opendevin.runtime.browser.browser_env import BrowserEnv

MAX_ITERATIONS = config.get(ConfigType.MAX_ITERATIONS)
MAX_CHARS = config.get(ConfigType.MAX_CHARS)


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    action_manager: ActionManager
    browser: BrowserEnv
    event_stream: EventStream
    delegate: 'AgentController | None' = None
    state: State | None = None
    _agent_state: AgentState = AgentState.INIT
    _cur_step: int = 0

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        sid: str = 'default',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
    ):
        """Initializes a new instance of the AgentController class.

        Args:
            agent: The agent instance to control.
            sid: The session ID of the agent.
            max_iterations: The maximum number of iterations the agent can run.
            max_chars: The maximum number of characters the agent can output.
        """
        self.id = sid
        self.agent = agent
        self.event_stream = event_stream
        self.event_stream.subscribe('agent_controller', self.on_event)
        self.max_iterations = max_iterations
        self.action_manager = ActionManager(self.id)
        self.max_chars = max_chars
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

    async def close(self):
        self.event_stream.unsubscribe('agent_controller')

    def update_state_for_step(self, i):
        if self.state is None:
            return
        self.state.iteration = i
        self.state.background_commands_obs = self.action_manager.get_background_obs()

    def update_state_after_step(self):
        if self.state is None:
            return
        self.state.updated_info = []

    async def add_error_to_history(self, message: str):
        await self.add_history(NullAction(), AgentErrorObservation(message))

    async def add_history(self, action: Action, observation: Observation):
        if self.state is None:
            raise ValueError('Added history while state was None')
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
        await self.event_stream.add_event(action, 'agent')
        await self.event_stream.add_event(observation, 'agent')

    async def _run(self):
        if self.state is None:
            return

        if self._agent_state != AgentState.RUNNING:
            raise ValueError('Task is not in running state')

        for i in range(self._cur_step, self.max_iterations):
            self._cur_step = i
            try:
                finished = await self.step(i)
                if finished:
                    await self.set_agent_state_to(AgentState.FINISHED)
                    break
            except Exception:
                logger.error('Error in loop', exc_info=True)
                await self.add_error_to_history(
                    'Oops! Something went wrong while completing your task. You can check the logs for more info.'
                )
                await self.set_agent_state_to(AgentState.STOPPED)
                break

            if self._is_stuck():
                logger.info('Loop detected, stopping task')
                await self.add_error_to_history(
                    'I got stuck into a loop, the task has stopped.'
                )
                await self.set_agent_state_to(AgentState.STOPPED)
                break

    async def setup_task(self, task: str, inputs: dict = {}):
        """Sets up the agent controller with a task."""
        await self.set_agent_state_to(AgentState.INIT)
        self.state = State(Plan(task))
        self.state.inputs = inputs

    async def on_event(self, event: Event):
        print('controller got event', event)
        if isinstance(event, ChangeAgentStateAction):
            if event.agent_state == AgentState.RUNNING:
                await self.set_agent_state_to(AgentState.RUNNING)
            elif event.agent_state == AgentState.PAUSED:
                await self.set_agent_state_to(AgentState.PAUSED)
            elif event.agent_state == AgentState.STOPPED:
                await self.set_agent_state_to(AgentState.STOPPED)
            elif event.agent_state == AgentState.FINISHED:
                await self.set_agent_state_to(AgentState.FINISHED)
            else:
                logger.warning(f'Unknown agent state: {event.agent_state}')
            await self.event_stream.add_event(
                AgentStateChangedObservation('', self._agent_state), 'agent'
            )

    async def reset_task(self):
        self.state = None
        self._cur_step = 0
        self._agent_state = AgentState.INIT
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState):
        logger.info(f'Setting agent state to {new_state}')
        if new_state == self._agent_state:
            return

        self._agent_state = new_state
        if new_state == AgentState.RUNNING:
            await self._run()
        elif new_state == AgentState.PAUSED:
            pass
        elif new_state == AgentState.STOPPED:
            await self.reset_task()
        elif new_state == AgentState.FINISHED:
            await self.reset_task()

    def get_agent_state(self):
        """Returns the current state of the agent task."""
        return self._agent_state

    async def add_user_message(self, message: UserMessageObservation):
        if self.state is None:
            return

        if self._agent_state == AgentState.AWAITING_USER_INPUT:
            self._await_user_message_queue.put_nowait(message)

            await self.set_agent_state_to(AgentState.RUNNING)

        elif self._agent_state == AgentState.RUNNING:
            await self.add_history(NullAction(), message)

        else:
            raise ValueError(
                f'Task (state: {self._agent_state}) is not in a state to add user message'
            )

    async def wait_for_user_input(self) -> UserMessageObservation:
        await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
        # FIXME: need a way to handle CLI input
        user_message_observation = await self._await_user_message_queue.get()
        self._await_user_message_queue.task_done()
        return user_message_observation

    async def start_delegate(self, action: AgentDelegateAction):
        AgentCls: Type[Agent] = Agent.get_cls(action.agent)
        agent = AgentCls(llm=self.agent.llm)
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=agent,
            event_stream=self.event_stream,
            max_iterations=self.max_iterations,
            max_chars=self.max_chars,
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
                await self.add_history(NullAction(), obs)
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
            await self.add_history(NullAction(), obs)
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

        # whether to await for user messages
        if isinstance(action, AgentTalkAction):
            # await for the next user messages
            user_message_observation = await self.wait_for_user_input()
            logger.info(user_message_observation, extra={'msg_type': 'OBSERVATION'})
            await self.add_history(action, user_message_observation)
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

        await self.add_history(action, observation)
        return False

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
