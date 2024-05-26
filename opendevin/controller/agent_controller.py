import asyncio
import traceback
from typing import Optional, Type

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.config import config
from opendevin.core.exceptions import (
    AgentMalformedActionError,
    AgentNoActionError,
    LLMOutputError,
    MaxCharsExceedError,
)
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.events import EventSource, EventStream, EventStreamSubscriber
from opendevin.events.action import (
    Action,
    AddTaskAction,
    AgentDelegateAction,
    AgentFinishAction,
    ChangeAgentStateAction,
    MessageAction,
    ModifyTaskAction,
    NullAction,
)
from opendevin.events.event import Event
from opendevin.events.observation import (
    AgentDelegateObservation,
    AgentStateChangedObservation,
    CmdOutputObservation,
    ErrorObservation,
    NullObservation,
    Observation,
)

MAX_ITERATIONS = config.max_iterations
MAX_CHARS = config.llm.max_chars


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    event_stream: EventStream
    state: State
    agent_task: Optional[asyncio.Task] = None
    delegate: 'AgentController | None' = None
    _pending_action: Action | None = None

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        sid: str = 'default',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        inputs: dict | None = None,
    ):
        """Initializes a new instance of the AgentController class.

        Args:
            agent: The agent instance to control.
            event_stream: The event stream to publish events to.
            sid: The session ID of the agent.
            max_iterations: The maximum number of iterations the agent can run.
            max_chars: The maximum number of characters the agent can output.
            inputs: The initial inputs to the agent.
        """
        self.id = sid
        self.agent = agent
        self.state = State(inputs=inputs or {}, max_iterations=max_iterations)
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.AGENT_CONTROLLER, self.on_event
        )
        self.max_iterations = max_iterations
        self.max_chars = max_chars
        self.agent_task = asyncio.create_task(self._start_step_loop())

    async def close(self):
        if self.agent_task is not None:
            self.agent_task.cancel()
        self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER)
        await self.set_agent_state_to(AgentState.STOPPED)

    def update_state_before_step(self):
        self.state.iteration += 1

    def update_state_after_step(self):
        self.state.updated_info = []
        # update metrics especially for cost
        self.state.metrics = self.agent.llm.metrics

    async def report_error(self, message: str, exception: Exception | None = None):
        self.state.error = message
        if exception:
            self.state.error += f': {str(exception)}'
        await self.event_stream.add_event(ErrorObservation(message), EventSource.AGENT)

    async def add_history(self, action: Action, observation: Observation):
        if isinstance(action, NullAction) and isinstance(observation, NullObservation):
            return
        self.state.history.append((action, observation))
        self.state.updated_info.append((action, observation))

    async def _start_step_loop(self):
        while True:
            try:
                await self._step()
            except asyncio.CancelledError:
                logger.info('AgentController task was cancelled')
                break
            except Exception as e:
                traceback.print_exc()
                logger.error(f'Error while running the agent: {e}')
                logger.error(traceback.format_exc())
                await self.report_error(
                    'There was an unexpected error while running the agent', exception=e
                )
                await self.set_agent_state_to(AgentState.ERROR)
                break

            await asyncio.sleep(0.1)

    async def on_event(self, event: Event):
        if isinstance(event, ChangeAgentStateAction):
            await self.set_agent_state_to(event.agent_state)  # type: ignore
        elif isinstance(event, MessageAction):
            if event.source == EventSource.USER:
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
                await self.add_history(event, NullObservation(''))
                if self.get_agent_state() != AgentState.RUNNING:
                    await self.set_agent_state_to(AgentState.RUNNING)
            elif event.source == EventSource.AGENT and event.wait_for_response:
                logger.info(event, extra={'msg_type': 'ACTION'})
                await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
        elif isinstance(event, AgentDelegateAction):
            await self.start_delegate(event)
        elif isinstance(event, AddTaskAction):
            self.state.root_task.add_subtask(event.parent, event.goal, event.subtasks)
        elif isinstance(event, ModifyTaskAction):
            self.state.root_task.set_subtask_state(event.task_id, event.state)
        elif isinstance(event, AgentFinishAction):
            self.state.outputs = event.outputs  # type: ignore[attr-defined]
            await self.set_agent_state_to(AgentState.FINISHED)
        elif isinstance(event, Observation):
            if self._pending_action and self._pending_action.id == event.cause:
                await self.add_history(self._pending_action, event)
                self._pending_action = None
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, CmdOutputObservation):
                await self.add_history(NullAction(), event)
                logger.info(event, extra={'msg_type': 'OBSERVATION'})

    def reset_task(self):
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState):
        logger.info(
            f'Setting agent({type(self.agent).__name__}) state from {self.state.agent_state} to {new_state}'
        )

        if new_state == self.state.agent_state:
            return

        self.state.agent_state = new_state
        if new_state == AgentState.STOPPED or new_state == AgentState.ERROR:
            self.reset_task()

        await self.event_stream.add_event(
            AgentStateChangedObservation('', self.state.agent_state), EventSource.AGENT
        )

        if new_state == AgentState.INIT and self.state.resume_state:
            await self.set_agent_state_to(self.state.resume_state)
            self.state.resume_state = None

    def get_agent_state(self):
        """Returns the current state of the agent task."""
        return self.state.agent_state

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

    async def _step(self):
        if self.get_agent_state() != AgentState.RUNNING:
            logger.debug('waiting for agent to run...')
            await asyncio.sleep(1)
            return

        if self._pending_action:
            logger.debug('waiting for pending action: ' + str(self._pending_action))
            await asyncio.sleep(1)
            return

        logger.info(f'STEP {self.state.iteration}', extra={'msg_type': 'STEP'})
        if self.state.iteration >= self.max_iterations:
            await self.report_error('Agent reached maximum number of iterations')
            await self.set_agent_state_to(AgentState.ERROR)
            return

        if self.delegate is not None:
            delegate_done = await self.delegate._step()
            if delegate_done:
                outputs = self.delegate.state.outputs if self.delegate.state else {}
                obs: Observation = AgentDelegateObservation(content='', outputs=outputs)
                await self.event_stream.add_event(obs, EventSource.AGENT)
                self.delegate = None
                self.delegateAction = None
            return

        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(self.state.num_of_chars, self.max_chars)

        self.update_state_before_step()
        action: Action = NullAction()
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise AgentNoActionError('No action was returned')
        except (AgentMalformedActionError, AgentNoActionError, LLMOutputError) as e:
            await self.report_error(str(e))
            return

        logger.info(action, extra={'msg_type': 'ACTION'})

        self.update_state_after_step()
        if action.runnable:
            self._pending_action = action
        else:
            await self.add_history(action, NullObservation(''))

        if not isinstance(action, NullAction):
            await self.event_stream.add_event(action, EventSource.AGENT)

        if self._is_stuck():
            await self.report_error('Agent got stuck in a loop')
            await self.set_agent_state_to(AgentState.ERROR)

    def get_state(self):
        return self.state

    def set_state(self, state: State):
        self.state = state

    def _is_stuck(self):
        # check if delegate stuck
        if self.delegate and self.delegate._is_stuck():
            return True

        # filter out MessageAction with source='user' from history
        filtered_history = [
            _tuple
            for _tuple in self.state.history
            if not (
                isinstance(_tuple[0], MessageAction)
                and _tuple[0].source == EventSource.USER
            )
        ]

        if len(filtered_history) < 4:
            return False

        # Check if the last four (Action, Observation) tuples are too repetitive
        last_four_tuples = filtered_history[-4:]
        if all(last_four_tuples[-1] == _tuple for _tuple in last_four_tuples):
            logger.warning('Action, Observation loop detected')
            return True

        if all(last_four_tuples[-1][0] == _tuple[0] for _tuple in last_four_tuples):
            # It repeats the same action, give it a chance, but not if:
            if all(
                isinstance(_tuple[1], ErrorObservation) for _tuple in last_four_tuples
            ):
                logger.warning('Action, ErrorObservation loop detected')
                return True

        # check if the agent repeats the same (Action, Observation)
        # every other step in the last six tuples
        if len(filtered_history) >= 6:
            last_six_tuples = filtered_history[-6:]
            if (
                last_six_tuples[-1] == last_six_tuples[-3] == last_six_tuples[-5]
                and last_six_tuples[-2] == last_six_tuples[-4] == last_six_tuples[-6]
            ):
                logger.warning('Action, Observation pattern detected')
                return True

        return False
