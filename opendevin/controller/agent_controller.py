import asyncio
import traceback
from typing import Optional, Type

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.controller.stuck import StuckDetector
from opendevin.core.config import config
from opendevin.core.exceptions import (
    LLMMalformedActionError,
    LLMNoActionError,
    LLMResponseError,
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
    AgentRejectAction,
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
    Observation,
)

MAX_ITERATIONS = config.max_iterations
MAX_CHARS = config.llm.max_chars
MAX_BUDGET_PER_TASK = config.max_budget_per_task


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    event_stream: EventStream
    state: State
    agent_task: Optional[asyncio.Task] = None
    parent: 'AgentController | None' = None
    delegate: 'AgentController | None' = None
    _pending_action: Action | None = None
    _stuck_detector: StuckDetector

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        sid: str = 'default',
        max_iterations: int = MAX_ITERATIONS,
        max_chars: int = MAX_CHARS,
        max_budget_per_task: float | None = MAX_BUDGET_PER_TASK,
        initial_state: State | None = None,
        is_delegate: bool = False,
    ):
        """Initializes a new instance of the AgentController class.

        Args:
            agent: The agent instance to control.
            event_stream: The event stream to publish events to.
            sid: The session ID of the agent.
            max_iterations: The maximum number of iterations the agent can run.
            max_chars: The maximum number of characters the agent can output.
            max_budget_per_task: The maximum budget (in USD) allowed per task, beyond which the agent will stop.
            initial_state: The initial state of the controller.
            is_delegate: Whether this controller is a delegate.
        """
        self._step_lock = asyncio.Lock()
        self.id = sid
        self.agent = agent
        self.max_chars = max_chars

        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, append=is_delegate
        )

        # state from the previous session, state from a parent agent, or a fresh state
        self._set_initial_state(
            state=initial_state,
            max_iterations=max_iterations,
        )

        self.max_budget_per_task = max_budget_per_task

        self._stuck_detector = StuckDetector(self.state)

        if not is_delegate:
            self.agent_task = asyncio.create_task(self._start_step_loop())

    async def close(self):
        if self.agent_task is not None:
            self.agent_task.cancel()
        await self.set_agent_state_to(AgentState.STOPPED)
        self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER)

    def update_state_before_step(self):
        self.state.iteration += 1

    async def update_state_after_step(self):
        # update metrics especially for cost
        self.state.metrics = self.agent.llm.metrics
        if self.max_budget_per_task is not None:
            current_cost = self.state.metrics.accumulated_cost
            if current_cost > self.max_budget_per_task:
                await self.report_error(
                    f'Task budget exceeded. Current cost: {current_cost:.2f}, Max budget: {self.max_budget_per_task:.2f}'
                )
                await self.set_agent_state_to(AgentState.ERROR)

    async def report_error(self, message: str, exception: Exception | None = None):
        """
        This error will be reported to the user and sent to the LLM next step, in the hope it can self-correct.

        This method should be called for a particular type of errors:
        - the string message should be user-friendly, it will be shown in the UI
        - an ErrorObservation can be sent to the LLM by the agent, with the exception message, so it can self-correct next time
        """
        if exception:
            message += f': {exception}'
        self.state.error = message
        self.event_stream.add_event(ErrorObservation(message), EventSource.AGENT)

    async def _start_step_loop(self):
        logger.info(f'[Agent Controller {self.id}] Starting step loop...')
        while True:
            try:
                await self._step()
            except asyncio.CancelledError:
                logger.info('AgentController task was cancelled')
                break
            except Exception as e:
                logger.error(f'Error while running the agent: {e}')
                logger.error(traceback.format_exc())
                await self.report_error(
                    'There was an unexpected error while running the agent', exception=e
                )
                await self.set_agent_state_to(AgentState.ERROR)
                break

            await asyncio.sleep(0.1)

    async def on_event(self, event: Event):
        logger.debug(f'AgentController on_event: {event}')
        if isinstance(event, ChangeAgentStateAction):
            await self.set_agent_state_to(event.agent_state)  # type: ignore
        elif isinstance(event, MessageAction):
            if event.source == EventSource.USER:
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
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
        elif isinstance(event, AgentRejectAction):
            self.state.outputs = event.outputs  # type: ignore[attr-defined]
            await self.set_agent_state_to(AgentState.REJECTED)
        elif isinstance(event, Observation):
            if self._pending_action and self._pending_action.id == event.cause:
                self._pending_action = None
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, CmdOutputObservation):
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, AgentDelegateObservation):
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, ErrorObservation):
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
                self.state.history.on_event(event)

    def reset_task(self):
        self.almost_stuck = 0
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState):
        logger.debug(
            f'[Agent Controller {self.id}] Setting agent({type(self.agent).__name__}) state from {self.state.agent_state} to {new_state}'
        )

        if new_state == self.state.agent_state:
            return

        self.state.agent_state = new_state
        if new_state == AgentState.STOPPED or new_state == AgentState.ERROR:
            self.reset_task()

        self.event_stream.add_event(
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
        state = State(
            inputs=action.inputs or {},
            iteration=0,
            max_iterations=self.state.max_iterations,
            num_of_chars=self.state.num_of_chars,
            delegate_level=self.state.delegate_level + 1,
            # metrics should be shared between parent and child
            metrics=self.state.metrics,
        )
        logger.info(f'[Agent Controller {self.id}]: start delegate')
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=agent,
            event_stream=self.event_stream,
            max_iterations=self.state.max_iterations,
            max_chars=self.max_chars,
            max_budget_per_task=self.max_budget_per_task,
            initial_state=state,
            is_delegate=True,
        )
        await self.delegate.set_agent_state_to(AgentState.RUNNING)

    async def _step(self):
        if self.get_agent_state() != AgentState.RUNNING:
            await asyncio.sleep(1)
            return

        if self._pending_action:
            logger.debug(
                f'[Agent Controller {self.id}] waiting for pending action: {self._pending_action}'
            )
            await asyncio.sleep(1)
            return

        if self.delegate is not None:
            logger.debug(f'[Agent Controller {self.id}] Delegate not none, awaiting...')
            assert self.delegate != self
            await self.delegate._step()
            logger.debug(f'[Agent Controller {self.id}] Delegate step done')
            assert self.delegate is not None
            delegate_state = self.delegate.get_agent_state()
            if delegate_state == AgentState.ERROR:
                # close the delegate upon error
                await self.delegate.close()
                await self.report_error('Delegator agent encounters an error')
                # propagate error state until an agent or user can handle it
                await self.set_agent_state_to(AgentState.ERROR)
                return
            delegate_done = delegate_state in (AgentState.FINISHED, AgentState.REJECTED)
            if delegate_done:
                logger.info(
                    f'[Agent Controller {self.id}] Delegate agent has finished execution'
                )
                # retrieve delegate result
                outputs = self.delegate.state.outputs if self.delegate.state else {}

                # close delegate controller: we must close the delegate controller before adding new events
                await self.delegate.close()

                # clean up delegate status
                self.delegate = None
                self.delegateAction = None

                # update delegate result observation
                obs: Observation = AgentDelegateObservation(outputs=outputs, content='')
                self.event_stream.add_event(obs, EventSource.AGENT)
            return

        if self.state.num_of_chars > self.max_chars:
            raise MaxCharsExceedError(self.state.num_of_chars, self.max_chars)

        logger.info(
            f'{type(self.agent).__name__} LEVEL {self.state.delegate_level} STEP {self.state.iteration}',
            extra={'msg_type': 'STEP'},
        )
        if self.state.iteration >= self.state.max_iterations:
            await self.report_error('Agent reached maximum number of iterations')
            await self.set_agent_state_to(AgentState.ERROR)
            return

        self.update_state_before_step()
        action: Action = NullAction()
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise LLMNoActionError('No action was returned')
        except (
            LLMMalformedActionError,
            LLMNoActionError,
            LLMResponseError,
        ) as e:
            # report to the user
            # and send the underlying exception to the LLM for self-correction
            await self.report_error(str(e))
            return

        logger.info(action, extra={'msg_type': 'ACTION'})

        if action.runnable:
            self._pending_action = action

        if not isinstance(action, NullAction):
            self.event_stream.add_event(action, EventSource.AGENT)

        await self.update_state_after_step()
        if self.state.agent_state == AgentState.ERROR:
            return

        if self._is_stuck():
            await self.report_error('Agent got stuck in a loop')
            await self.set_agent_state_to(AgentState.ERROR)

    def get_state(self):
        return self.state

    def _set_initial_state(
        self,
        state: State | None = None,
        max_iterations: int = MAX_ITERATIONS,
    ):
        # state from the previous session, state from a parent agent, or a new state
        # note that this is called twice when restoring a previous session, first with state=None
        if state is None:
            self.state = State(inputs={}, max_iterations=max_iterations)
        else:
            self.state = state

        # when restored from a previous session, the State object will have history, start_id, and end_id
        # connect it to the event stream
        self.state.history.set_event_stream(self.event_stream)

        # if start_id was not set in State, we're starting fresh, at the top of the stream
        start_id = self.state.start_id
        if start_id == -1:
            start_id = self.event_stream.get_latest_event_id() + 1
        else:
            logger.debug(f'AgentController {self.id} restoring from event {start_id}')

        # make sure history is in sync
        self.state.start_id = start_id
        self.state.history.start_id = start_id

        # if there was an end_id saved in State, set it in history
        # currently used only for delegates internally in history
        if self.state.end_id > -1:
            self.state.history.end_id = self.state.end_id

    def __repr__(self):
        return (
            f'AgentController(id={self.id}, agent={self.agent!r}, '
            f'event_stream={self.event_stream!r}, '
            f'state={self.state!r}, agent_task={self.agent_task!r}, '
            f'delegate={self.delegate!r}, _pending_action={self._pending_action!r})'
        )

    def _is_stuck(self):
        # check if delegate stuck
        if self.delegate and self.delegate._is_stuck():
            return True

        return self._stuck_detector.is_stuck()
