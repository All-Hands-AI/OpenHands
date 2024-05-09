import asyncio
from typing import Optional, Type

from agenthub.codeact_agent.codeact_agent import CodeActAgent
from opendevin.controller.action_manager import ActionManager
from opendevin.controller.agent import Agent
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
    AgentRejectAction,
    ChangeAgentStateAction,
    MessageAction,
    NullAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    AgentDelegateObservation,
    AgentStateChangedObservation,
    ErrorObservation,
    NullObservation,
    Observation,
)
from opendevin.events.stream import EventSource, EventStream, EventStreamSubscriber
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
    agent_task: Optional[asyncio.Task] = None
    delegate: 'AgentController | None' = None
    state: State | None = None
    _agent_state: AgentState = AgentState.LOADING
    _cur_step: int = 0

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        sid: str = 'default',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        inputs: Optional[dict] = None,
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
        self.state = State(inputs=inputs or {})
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.AGENT_CONTROLLER, self.on_event
        )
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

    async def close(self):
        if self.agent_task is not None:
            self.agent_task.cancel()
        self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER)
        self.action_manager.sandbox.close()
        await self.set_agent_state_to(AgentState.STOPPED)

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
        await self.add_history(NullAction(), ErrorObservation(message))

    async def add_history(
        self, action: Action, observation: Observation, add_to_stream=True
    ):
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
        if add_to_stream:
            await self.event_stream.add_event(action, EventSource.AGENT)
            await self.event_stream.add_event(observation, EventSource.AGENT)

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
                await self.set_agent_state_to(AgentState.ERROR)
                await self.add_error_to_history(
                    'Oops! Something went wrong while completing your task. You can check the logs for more info.'
                )
                break

            if self._is_stuck():
                logger.info('Loop detected, stopping task')
                await self.set_agent_state_to(AgentState.ERROR)
                await self.add_error_to_history(
                    'I got stuck into a loop, the task has stopped.'
                )
                break
            await asyncio.sleep(
                0.001
            )  # Give back control for a tick, so other async stuff can run
        final_state = self.get_agent_state()
        if final_state == AgentState.RUNNING:
            await self.set_agent_state_to(AgentState.PAUSED)

    async def on_event(self, event: Event):
        if isinstance(event, ChangeAgentStateAction):
            await self.set_agent_state_to(event.agent_state)  # type: ignore
        elif isinstance(event, MessageAction) and event.source == EventSource.USER:
            await self.add_history(event, NullObservation(''), add_to_stream=False)
            if self.get_agent_state() != AgentState.RUNNING:
                await self.set_agent_state_to(AgentState.RUNNING)

    async def reset_task(self):
        if self.agent_task is not None:
            self.agent_task.cancel()
        self.state = None
        self._cur_step = 0
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState):
        logger.info(f'Setting agent state from {self._agent_state} to {new_state}')
        if new_state == self._agent_state:
            return

        self._agent_state = new_state
        if new_state == AgentState.RUNNING:
            self.agent_task = asyncio.create_task(self._run())
        elif (
            new_state == AgentState.PAUSED
            or new_state == AgentState.AWAITING_USER_INPUT
        ):
            self._cur_step += 1
            if self.agent_task is not None:
                self.agent_task.cancel()
        elif new_state == AgentState.STOPPED:
            await self.reset_task()

        await self.event_stream.add_event(
            AgentStateChangedObservation('', self._agent_state), EventSource.AGENT
        )

    def get_agent_state(self):
        """Returns the current state of the agent task."""
        return self._agent_state

    async def start_delegate(self, action: AgentDelegateAction):
        AgentCls: Type[Agent] = Agent.get_cls(action.agent)
        agent = AgentCls(llm=self.agent.llm)
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=agent,
            event_stream=self.event_stream,
            max_iterations=self.max_iterations,
            max_chars=self.max_chars,
            inputs=action.inputs,
        )

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
            observation = ErrorObservation(str(e))
        logger.info(action, extra={'msg_type': 'ACTION'})

        self.update_state_after_step()

        if isinstance(action, MessageAction) and action.wait_for_response:
            # FIXME: remove this once history is managed outside the agent controller
            await self.add_history(action, NullObservation(''))
            await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
            return False

        finished = isinstance(action, AgentFinishAction) or isinstance(
            action, AgentRejectAction
        )
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
                isinstance(self.state.history[-i][1], ErrorObservation)
                for i in range(1, 4)
            ):
                # (NullAction, ErrorObservation): errors coming from an exception
                # (Action, ErrorObservation): the same action getting an error, even if not necessarily the same error
                logger.debug('Action, ErrorObservation loop detected')
                return True

        return False
