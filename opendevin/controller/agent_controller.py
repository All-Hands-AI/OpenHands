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
    AgentRejectAction,
    ChangeAgentStateAction,
    MessageAction,
    ModifyTaskAction,
    NullAction,
)
from opendevin.events.action.commands import CmdKillAction
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
        if initial_state is None:
            self.state = State(inputs={}, max_iterations=max_iterations)
        else:
            self.state = initial_state
        self.event_stream = event_stream
        self.event_stream.subscribe(
            EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, append=is_delegate
        )
        self.max_budget_per_task = max_budget_per_task
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
        self.state.updated_info = []
        # update metrics especially for cost
        self.state.metrics = self.agent.llm.metrics
        if self.max_budget_per_task is not None:
            current_cost = self.state.metrics.accumulated_cost
            if current_cost > self.max_budget_per_task:
                await self.report_error(
                    f'Task budget exceeded. Current cost: {current_cost}, Max budget: {self.max_budget_per_task}'
                )
                await self.set_agent_state_to(AgentState.ERROR)

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
        logger.info(f'[Agent Controller {self.id}] Starting step loop...')
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
        elif isinstance(event, AgentRejectAction):
            self.state.outputs = event.outputs  # type: ignore[attr-defined]
            await self.set_agent_state_to(AgentState.REJECTED)
        elif isinstance(event, Observation):
            if self._pending_action and self._pending_action.id == event.cause:
                await self.add_history(self._pending_action, event)
                self._pending_action = None
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, CmdOutputObservation):
                await self.add_history(NullAction(), event)
                logger.info(event, extra={'msg_type': 'OBSERVATION'})
            elif isinstance(event, AgentDelegateObservation):
                await self.add_history(NullAction(), event)
                logger.info(event, extra={'msg_type': 'OBSERVATION'})

    def reset_task(self):
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState):
        logger.info(
            f'[Agent Controller {self.id}] Setting agent({type(self.agent).__name__}) state from {self.state.agent_state} to {new_state}'
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
        state = State(
            inputs=action.inputs or {},
            iteration=0,
            max_iterations=self.state.max_iterations,
            num_of_chars=self.state.num_of_chars,
            delegate_level=self.state.delegate_level + 1,
        )
        logger.info(f'[Agent Controller {self.id}]: start delegate')
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=agent,
            event_stream=self.event_stream,
            max_iterations=self.state.max_iterations,
            max_chars=self.max_chars,
            initial_state=state,
            is_delegate=True,
        )
        await self.delegate.set_agent_state_to(AgentState.RUNNING)

    async def _step(self):
        logger.debug(f'[Agent Controller {self.id}] Entering step method')
        if self.get_agent_state() != AgentState.RUNNING:
            await asyncio.sleep(1)
            return

        if self._pending_action:
            logger.info(
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
                await self.event_stream.add_event(obs, EventSource.AGENT)
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
                raise AgentNoActionError('No action was returned')
        except (AgentMalformedActionError, AgentNoActionError, LLMOutputError) as e:
            await self.report_error(str(e))
            return

        logger.info(action, extra={'msg_type': 'ACTION'})

        await self.update_state_after_step()
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

        if len(filtered_history) < 3:
            return False

        # FIXME rewrite this to be more readable

        # Scenario 1: the same (Action, Observation) loop
        # 3 pairs of (action, observation) to stop the agent
        last_three_tuples = filtered_history[-3:]

        if all(
            # (Action, Observation) tuples
            # compare the last action to the last three actions
            self._eq_no_pid(last_three_tuples[-1][0], _tuple[0])
            for _tuple in last_three_tuples
        ) and all(
            # compare the last observation to the last three observations
            self._eq_no_pid(last_three_tuples[-1][1], _tuple[1])
            for _tuple in last_three_tuples
        ):
            logger.warning('Action, Observation loop detected')
            return True

        if len(filtered_history) < 4:
            return False

        last_four_tuples = filtered_history[-4:]

        # Scenario 2: (action, error) pattern, not necessary identical error
        # 4 pairs of (action, error) to stop the agent
        if all(
            self._eq_no_pid(last_four_tuples[-1][0], _tuple[0])
            for _tuple in last_four_tuples
        ):
            # It repeats the same action, give it a chance, but not if:
            if all(
                isinstance(_tuple[1], ErrorObservation) for _tuple in last_four_tuples
            ):
                logger.warning('Action, ErrorObservation loop detected')
                return True

        # check if the agent repeats the same (Action, Observation)
        # every other step in the last six tuples
        # step1 = step3 = step5
        # step2 = step4 = step6
        if len(filtered_history) >= 6:
            last_six_tuples = filtered_history[-6:]
            if (
                # this pattern is every other step, like:
                # (action_1, obs_1), (action_2, obs_2), (action_1, obs_1), (action_2, obs_2),...
                self._eq_no_pid(last_six_tuples[-1][0], last_six_tuples[-3][0])
                and self._eq_no_pid(last_six_tuples[-1][0], last_six_tuples[-5][0])
                and self._eq_no_pid(last_six_tuples[-2][0], last_six_tuples[-4][0])
                and self._eq_no_pid(last_six_tuples[-2][0], last_six_tuples[-6][0])
                and self._eq_no_pid(last_six_tuples[-1][1], last_six_tuples[-3][1])
                and self._eq_no_pid(last_six_tuples[-1][1], last_six_tuples[-5][1])
                and self._eq_no_pid(last_six_tuples[-2][1], last_six_tuples[-4][1])
                and self._eq_no_pid(last_six_tuples[-2][1], last_six_tuples[-6][1])
            ):
                logger.warning('Action, Observation pattern detected')
                return True

        return False

    def __repr__(self):
        return (
            f'AgentController(id={self.id}, agent={self.agent!r}, '
            f'event_stream={self.event_stream!r}, '
            f'state={self.state!r}, agent_task={self.agent_task!r}, '
            f'delegate={self.delegate!r}, _pending_action={self._pending_action!r})'
        )

    def _eq_no_pid(self, obj1, obj2):
        if isinstance(obj1, CmdOutputObservation) and isinstance(
            obj2, CmdOutputObservation
        ):
            # for loop detection, ignore command_id, which is the pid
            return obj1.command == obj2.command and obj1.exit_code == obj2.exit_code
        elif isinstance(obj1, CmdKillAction) and isinstance(obj2, CmdKillAction):
            # for loop detection, ignore command_id, which is the pid
            return obj1.thought == obj2.thought
        else:
            # this is the default comparison
            return obj1 == obj2
