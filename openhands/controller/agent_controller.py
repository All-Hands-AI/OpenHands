from __future__ import annotations

import asyncio
import copy
import os
import time
import traceback
from typing import Callable, ClassVar

import litellm  # noqa
from litellm.exceptions import (  # noqa
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    ContentPolicyViolationError,
    ContextWindowExceededError,
    InternalServerError,
    NotFoundError,
    OpenAIError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from openhands.controller.agent import Agent
from openhands.controller.replay import ReplayManager
from openhands.controller.state.state import State, TrafficControlState
from openhands.controller.stuck import StuckDetector
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.exceptions import (
    AgentStuckInLoopError,
    FunctionCallNotExistsError,
    FunctionCallValidationError,
    LLMContextWindowExceedError,
    LLMMalformedActionError,
    LLMNoActionError,
    LLMResponseError,
)
from openhands.core.logger import LOG_ALL_EVENTS
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.events import (
    EventSource,
    EventStream,
    EventStreamSubscriber,
    RecallType,
)
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    AgentDelegateAction,
    AgentFinishAction,
    AgentRejectAction,
    ChangeAgentStateAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
    NullAction,
    SystemMessageAction,
)
from openhands.events.action.agent import CondensationAction, RecallAction
from openhands.events.event import Event
from openhands.events.observation import (
    AgentDelegateObservation,
    AgentStateChangedObservation,
    ErrorObservation,
    NullObservation,
    Observation,
)
from openhands.events.serialization.event import event_to_trajectory, truncate_content
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics, TokenUsage

# note: RESUME is only available on web GUI
TRAFFIC_CONTROL_REMINDER = (
    "Please click on resume button if you'd like to continue, or start a new task."
)
ERROR_ACTION_NOT_EXECUTED_ID = 'AGENT_ERROR$ERROR_ACTION_NOT_EXECUTED'
ERROR_ACTION_NOT_EXECUTED = 'The action has not been executed. This may have occurred because the user pressed the stop button, or because the runtime system crashed and restarted due to resource constraints. Any previously established system state, dependencies, or environment variables may have been lost.'


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    event_stream: EventStream
    state: State
    confirmation_mode: bool
    agent_to_llm_config: dict[str, LLMConfig]
    agent_configs: dict[str, AgentConfig]
    parent: 'AgentController | None' = None
    delegate: 'AgentController | None' = None
    _pending_action_info: tuple[Action, float] | None = None  # (action, timestamp)
    _closed: bool = False
    filter_out: ClassVar[tuple[type[Event], ...]] = (
        NullAction,
        NullObservation,
        ChangeAgentStateAction,
        AgentStateChangedObservation,
    )
    _cached_first_user_message: MessageAction | None = None

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        sid: str | None = None,
        confirmation_mode: bool = False,
        initial_state: State | None = None,
        is_delegate: bool = False,
        headless_mode: bool = True,
        status_callback: Callable | None = None,
        replay_events: list[Event] | None = None,
    ):
        """Initializes a new instance of the AgentController class.

        Args:
            agent: The agent instance to control.
            event_stream: The event stream to publish events to.
            max_iterations: The maximum number of iterations the agent can run.
            max_budget_per_task: The maximum budget (in USD) allowed per task, beyond which the agent will stop.
            agent_to_llm_config: A dictionary mapping agent names to LLM configurations in the case that
                we delegate to a different agent.
            agent_configs: A dictionary mapping agent names to agent configurations in the case that
                we delegate to a different agent.
            sid: The session ID of the agent.
            confirmation_mode: Whether to enable confirmation mode for agent actions.
            initial_state: The initial state of the controller.
            is_delegate: Whether this controller is a delegate.
            headless_mode: Whether the agent is run in headless mode.
            status_callback: Optional callback function to handle status updates.
            replay_events: A list of logs to replay.
        """
        self.id = sid or event_stream.sid
        self.agent = agent
        self.headless_mode = headless_mode
        self.is_delegate = is_delegate

        # the event stream must be set before maybe subscribing to it
        self.event_stream = event_stream

        # subscribe to the event stream if this is not a delegate
        if not self.is_delegate:
            self.event_stream.subscribe(
                EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, self.id
            )

        # state from the previous session, state from a parent agent, or a fresh state
        self.set_initial_state(
            state=initial_state,
            max_iterations=max_iterations,
            confirmation_mode=confirmation_mode,
        )
        self.max_budget_per_task = max_budget_per_task
        self.agent_to_llm_config = agent_to_llm_config if agent_to_llm_config else {}
        self.agent_configs = agent_configs if agent_configs else {}
        self._initial_max_iterations = max_iterations
        self._initial_max_budget_per_task = max_budget_per_task

        # stuck helper
        self._stuck_detector = StuckDetector(self.state)
        self.status_callback = status_callback

        # replay-related
        self._replay_manager = ReplayManager(replay_events)

        # Add the system message to the event stream
        self._add_system_message()

    def _add_system_message(self):
        for event in self.event_stream.get_events(start_id=self.state.start_id):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                # FIXME: Remove this after 6/1/2025
                # Do not try to add a system message if we first run into
                # a user message -- this means the eventstream exits before
                # SystemMessageAction is introduced.
                # We expect *agent* to handle this case gracefully.
                return

            if isinstance(event, SystemMessageAction):
                # Do not try to add the system message if it already exists
                return

        # Add the system message to the event stream
        # This should be done for all agents, including delegates
        system_message = self.agent.get_system_message()
        logger.debug(f'System message got from agent: {system_message}')
        if system_message:
            self.event_stream.add_event(system_message, EventSource.AGENT)
            logger.info(f'System message added to event stream: {system_message}')

    async def close(self, set_stop_state: bool = True) -> None:
        """Closes the agent controller, canceling any ongoing tasks and unsubscribing from the event stream.

        Note that it's fairly important that this closes properly, otherwise the state is incomplete.
        """
        if set_stop_state:
            await self.set_agent_state_to(AgentState.STOPPED)

        # we made history, now is the time to rewrite it!
        # the final state.history will be used by external scripts like evals, tests, etc.
        # history will need to be complete WITH delegates events
        # like the regular agent history, it does not include:
        # - 'hidden' events, events with hidden=True
        # - backend events (the default 'filtered out' types, types in self.filter_out)
        start_id = self.state.start_id if self.state.start_id >= 0 else 0
        end_id = (
            self.state.end_id
            if self.state.end_id >= 0
            else self.event_stream.get_latest_event_id()
        )
        self.state.history = list(
            self.event_stream.get_events(
                start_id=start_id,
                end_id=end_id,
                reverse=False,
                filter_out_type=self.filter_out,
                filter_hidden=True,
            )
        )

        # unsubscribe from the event stream
        # only the root parent controller subscribes to the event stream
        if not self.is_delegate:
            self.event_stream.unsubscribe(
                EventStreamSubscriber.AGENT_CONTROLLER, self.id
            )
        self._closed = True

    def log(self, level: str, message: str, extra: dict | None = None) -> None:
        """Logs a message to the agent controller's logger.

        Args:
            level (str): The logging level to use (e.g., 'info', 'debug', 'error').
            message (str): The message to log.
            extra (dict | None, optional): Additional fields to log. Includes session_id by default.
        """
        message = f'[Agent Controller {self.id}] {message}'
        if extra is None:
            extra = {}
        extra_merged = {'session_id': self.id, **extra}
        getattr(logger, level)(message, extra=extra_merged, stacklevel=2)

    def update_state_before_step(self) -> None:
        self.state.iteration += 1
        self.state.local_iteration += 1

    async def update_state_after_step(self) -> None:
        # update metrics especially for cost. Use deepcopy to avoid it being modified by agent._reset()
        self.state.local_metrics = copy.deepcopy(self.agent.llm.metrics)

    async def _react_to_exception(
        self,
        e: Exception,
    ) -> None:
        """React to an exception by setting the agent state to error and sending a status message."""
        # Store the error reason before setting the agent state
        self.state.last_error = f'{type(e).__name__}: {str(e)}'

        if self.status_callback is not None:
            err_id = ''
            if isinstance(e, AuthenticationError):
                err_id = 'STATUS$ERROR_LLM_AUTHENTICATION'
                self.state.last_error = err_id
            elif isinstance(
                e,
                (
                    ServiceUnavailableError,
                    APIConnectionError,
                    APIError,
                ),
            ):
                err_id = 'STATUS$ERROR_LLM_SERVICE_UNAVAILABLE'
                self.state.last_error = err_id
            elif isinstance(e, InternalServerError):
                err_id = 'STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR'
                self.state.last_error = err_id
            elif isinstance(e, BadRequestError) and 'ExceededBudget' in str(e):
                err_id = 'STATUS$ERROR_LLM_OUT_OF_CREDITS'
                self.state.last_error = err_id
            elif isinstance(e, ContentPolicyViolationError) or (
                isinstance(e, BadRequestError)
                and 'ContentPolicyViolationError' in str(e)
            ):
                err_id = 'STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION'
                self.state.last_error = err_id
            elif isinstance(e, RateLimitError):
                await self.set_agent_state_to(AgentState.RATE_LIMITED)
                return
            self.status_callback('error', err_id, self.state.last_error)

        # Set the agent state to ERROR after storing the reason
        await self.set_agent_state_to(AgentState.ERROR)

    def step(self) -> None:
        asyncio.create_task(self._step_with_exception_handling())

    async def _step_with_exception_handling(self) -> None:
        try:
            await self._step()
        except Exception as e:
            self.log(
                'error',
                f'Error while running the agent (session ID: {self.id}): {e}. '
                f'Traceback: {traceback.format_exc()}',
            )
            reported = RuntimeError(
                f'There was an unexpected error while running the agent: {e.__class__.__name__}. You can refresh the page or ask the agent to try again.'
            )
            if (
                isinstance(e, Timeout)
                or isinstance(e, APIError)
                or isinstance(e, BadRequestError)
                or isinstance(e, NotFoundError)
                or isinstance(e, InternalServerError)
                or isinstance(e, AuthenticationError)
                or isinstance(e, RateLimitError)
                or isinstance(e, ContentPolicyViolationError)
                or isinstance(e, LLMContextWindowExceedError)
            ):
                reported = e
            else:
                self.log(
                    'warning',
                    f'Unknown exception type while running the agent: {type(e).__name__}.',
                )
            await self._react_to_exception(reported)

    def should_step(self, event: Event) -> bool:
        """Whether the agent should take a step based on an event.

        In general, the agent should take a step if it receives a message from the user,
        or observes something in the environment (after acting).
        """
        # it might be the delegate's day in the sun
        if self.delegate is not None:
            return False

        if isinstance(event, Action):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return True
            if (
                isinstance(event, MessageAction)
                and self.get_agent_state() != AgentState.AWAITING_USER_INPUT
            ):
                # TODO: this is fragile, but how else to check if eligible?
                return True
            if isinstance(event, AgentDelegateAction):
                return True
            if isinstance(event, CondensationAction):
                return True
            return False
        if isinstance(event, Observation):
            if (
                isinstance(event, NullObservation)
                and event.cause is not None
                and event.cause
                > 0  # NullObservation has cause > 0 (RecallAction), not 0 (user message)
            ):
                return True
            if isinstance(event, AgentStateChangedObservation) or isinstance(
                event, NullObservation
            ):
                return False
            return True
        return False

    def on_event(self, event: Event) -> None:
        """Callback from the event stream. Notifies the controller of incoming events.

        Args:
            event (Event): The incoming event to process.
        """
        # If we have a delegate that is not finished or errored, forward events to it
        if self.delegate is not None:
            delegate_state = self.delegate.get_agent_state()
            if delegate_state not in (
                AgentState.FINISHED,
                AgentState.ERROR,
                AgentState.REJECTED,
            ):
                # Forward the event to delegate and skip parent processing
                asyncio.get_event_loop().run_until_complete(
                    self.delegate._on_event(event)
                )
                return
            else:
                # delegate is done or errored, so end it
                self.end_delegate()
                return

        # continue parent processing only if there's no active delegate
        asyncio.get_event_loop().run_until_complete(self._on_event(event))

    async def _on_event(self, event: Event) -> None:
        if hasattr(event, 'hidden') and event.hidden:
            return

        # Give others a little chance
        await asyncio.sleep(0.01)

        # if the event is not filtered out, add it to the history
        if not any(isinstance(event, filter_type) for filter_type in self.filter_out):
            self.state.history.append(event)

        if isinstance(event, Action):
            await self._handle_action(event)
        elif isinstance(event, Observation):
            await self._handle_observation(event)

        should_step = self.should_step(event)
        if should_step:
            self.log(
                'debug',
                f'Stepping agent after event: {type(event).__name__}',
                extra={'msg_type': 'STEPPING_AGENT'},
            )
            await self._step_with_exception_handling()
        elif isinstance(event, MessageAction) and event.source == EventSource.USER:
            # If we received a user message but aren't stepping, log why
            self.log(
                'warning',
                f'Not stepping agent after user message. Current state: {self.get_agent_state()}',
                extra={'msg_type': 'NOT_STEPPING_AFTER_USER_MESSAGE'},
            )

    async def _handle_action(self, action: Action) -> None:
        """Handles an Action from the agent or delegate."""
        if isinstance(action, ChangeAgentStateAction):
            await self.set_agent_state_to(action.agent_state)  # type: ignore
        elif isinstance(action, MessageAction):
            await self._handle_message_action(action)
        elif isinstance(action, AgentDelegateAction):
            await self.start_delegate(action)
            assert self.delegate is not None
            # Post a MessageAction with the task for the delegate
            if 'task' in action.inputs:
                self.event_stream.add_event(
                    MessageAction(content='TASK: ' + action.inputs['task']),
                    EventSource.USER,
                )
                await self.delegate.set_agent_state_to(AgentState.RUNNING)
            return

        elif isinstance(action, AgentFinishAction):
            self.state.outputs = action.outputs
            self.state.metrics.merge(self.state.local_metrics)
            await self.set_agent_state_to(AgentState.FINISHED)
        elif isinstance(action, AgentRejectAction):
            self.state.outputs = action.outputs
            self.state.metrics.merge(self.state.local_metrics)
            await self.set_agent_state_to(AgentState.REJECTED)

    async def _handle_observation(self, observation: Observation) -> None:
        """Handles observation from the event stream.

        Args:
            observation (observation): The observation to handle.
        """
        observation_to_print = copy.deepcopy(observation)
        if len(observation_to_print.content) > self.agent.llm.config.max_message_chars:
            observation_to_print.content = truncate_content(
                observation_to_print.content, self.agent.llm.config.max_message_chars
            )
        # Use info level if LOG_ALL_EVENTS is set
        log_level = 'info' if os.getenv('LOG_ALL_EVENTS') in ('true', '1') else 'debug'
        self.log(
            log_level, str(observation_to_print), extra={'msg_type': 'OBSERVATION'}
        )

        if observation.llm_metrics is not None:
            self.agent.llm.metrics.merge(observation.llm_metrics)

        # this happens for runnable actions and microagent actions
        if self._pending_action and self._pending_action.id == observation.cause:
            if self.state.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                return

            self._pending_action = None

            if self.state.agent_state == AgentState.USER_CONFIRMED:
                await self.set_agent_state_to(AgentState.RUNNING)
            if self.state.agent_state == AgentState.USER_REJECTED:
                await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)
            return
        elif isinstance(observation, ErrorObservation):
            if self.state.agent_state == AgentState.ERROR:
                self.state.metrics.merge(self.state.local_metrics)

    async def _handle_message_action(self, action: MessageAction) -> None:
        """Handles message actions from the event stream.

        Args:
            action (MessageAction): The message action to handle.
        """
        if action.source == EventSource.USER:
            # Use info level if LOG_ALL_EVENTS is set
            log_level = (
                'info' if os.getenv('LOG_ALL_EVENTS') in ('true', '1') else 'debug'
            )
            self.log(
                log_level,
                str(action),
                extra={'msg_type': 'ACTION', 'event_source': EventSource.USER},
            )
            # Extend max iterations when the user sends a message (only in non-headless mode)
            if self._initial_max_iterations is not None and not self.headless_mode:
                self.state.max_iterations = (
                    self.state.iteration + self._initial_max_iterations
                )
                if (
                    self.state.traffic_control_state == TrafficControlState.THROTTLING
                    or self.state.traffic_control_state == TrafficControlState.PAUSED
                ):
                    self.state.traffic_control_state = TrafficControlState.NORMAL
                self.log(
                    'debug',
                    f'Extended max iterations to {self.state.max_iterations} after user message',
                )
            # try to retrieve microagents relevant to the user message
            # set pending_action while we search for information

            # if this is the first user message for this agent, matters for the microagent info type
            first_user_message = self._first_user_message()
            is_first_user_message = (
                action.id == first_user_message.id if first_user_message else False
            )
            recall_type = (
                RecallType.WORKSPACE_CONTEXT
                if is_first_user_message
                else RecallType.KNOWLEDGE
            )

            recall_action = RecallAction(query=action.content, recall_type=recall_type)
            self._pending_action = recall_action
            # this is source=USER because the user message is the trigger for the microagent retrieval
            self.event_stream.add_event(recall_action, EventSource.USER)

            if self.get_agent_state() != AgentState.RUNNING:
                await self.set_agent_state_to(AgentState.RUNNING)

        elif action.source == EventSource.AGENT:
            # If the agent is waiting for a response, set the appropriate state
            if action.wait_for_response:
                await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)

    def _reset(self) -> None:
        """Resets the agent controller."""
        # Runnable actions need an Observation
        # make sure there is an Observation with the tool call metadata to be recognized by the agent
        # otherwise the pending action is found in history, but it's incomplete without an obs with tool result
        if self._pending_action and hasattr(self._pending_action, 'tool_call_metadata'):
            # find out if there already is an observation with the same tool call metadata
            found_observation = False
            for event in self.state.history:
                if (
                    isinstance(event, Observation)
                    and event.tool_call_metadata
                    == self._pending_action.tool_call_metadata
                ):
                    found_observation = True
                    break

            # make a new ErrorObservation with the tool call metadata
            if not found_observation:
                obs = ErrorObservation(
                    content=ERROR_ACTION_NOT_EXECUTED,
                    error_id=ERROR_ACTION_NOT_EXECUTED_ID,
                )
                obs.tool_call_metadata = self._pending_action.tool_call_metadata
                obs._cause = self._pending_action.id  # type: ignore[attr-defined]
                self.event_stream.add_event(obs, EventSource.AGENT)

        # NOTE: RecallActions don't need an ErrorObservation upon reset, as long as they have no tool calls

        # reset the pending action, this will be called when the agent is STOPPED or ERROR
        self._pending_action = None
        self.agent.reset()

    async def set_agent_state_to(self, new_state: AgentState) -> None:
        """Updates the agent's state and handles side effects. Can emit events to the event stream.

        Args:
            new_state (AgentState): The new state to set for the agent.
        """
        self.log(
            'info',
            f'Setting agent({self.agent.name}) state from {self.state.agent_state} to {new_state}',
        )

        if new_state == self.state.agent_state:
            return

        if new_state in (AgentState.STOPPED, AgentState.ERROR):
            # sync existing metrics BEFORE resetting the agent
            await self.update_state_after_step()
            self.state.metrics.merge(self.state.local_metrics)
            self._reset()
        elif (
            new_state == AgentState.RUNNING
            and self.state.agent_state == AgentState.PAUSED
            # TODO: do we really need both THROTTLING and PAUSED states, or can we clean up one of them completely?
            and self.state.traffic_control_state == TrafficControlState.THROTTLING
        ):
            # user intends to interrupt traffic control and let the task resume temporarily
            self.state.traffic_control_state = TrafficControlState.PAUSED
            # User has chosen to deliberately continue - lets double the max iterations
            if (
                self.state.iteration is not None
                and self.state.max_iterations is not None
                and self._initial_max_iterations is not None
                and not self.headless_mode
            ):
                if self.state.iteration >= self.state.max_iterations:
                    self.state.max_iterations += self._initial_max_iterations

            if (
                self.state.metrics.accumulated_cost is not None
                and self.max_budget_per_task is not None
                and self._initial_max_budget_per_task is not None
            ):
                if self.state.metrics.accumulated_cost >= self.max_budget_per_task:
                    self.max_budget_per_task += self._initial_max_budget_per_task
        elif self._pending_action is not None and (
            new_state in (AgentState.USER_CONFIRMED, AgentState.USER_REJECTED)
        ):
            if hasattr(self._pending_action, 'thought'):
                self._pending_action.thought = ''  # type: ignore[union-attr]
            if new_state == AgentState.USER_CONFIRMED:
                confirmation_state = ActionConfirmationStatus.CONFIRMED
            else:
                confirmation_state = ActionConfirmationStatus.REJECTED
            self._pending_action.confirmation_state = confirmation_state  # type: ignore[attr-defined]
            self._pending_action._id = None  # type: ignore[attr-defined]
            self.event_stream.add_event(self._pending_action, EventSource.AGENT)

        self.state.agent_state = new_state

        # Create observation with reason field if it's an error state
        reason = ''
        if new_state == AgentState.ERROR:
            reason = self.state.last_error

        self.event_stream.add_event(
            AgentStateChangedObservation('', self.state.agent_state, reason),
            EventSource.ENVIRONMENT,
        )

    def get_agent_state(self) -> AgentState:
        """Returns the current state of the agent.

        Returns:
            AgentState: The current state of the agent.
        """
        return self.state.agent_state

    async def start_delegate(self, action: AgentDelegateAction) -> None:
        """Start a delegate agent to handle a subtask.

        OpenHands is a multi-agentic system. A `task` is a conversation between
        OpenHands (the whole system) and the user, which might involve one or more inputs
        from the user. It starts with an initial input (typically a task statement) from
        the user, and ends with either an `AgentFinishAction` initiated by the agent, a
        stop initiated by the user, or an error.

        A `subtask` is a conversation between an agent and the user, or another agent. If a `task`
        is conducted by a single agent, then it's also a `subtask`. Otherwise, a `task` consists of
        multiple `subtasks`, each executed by one agent.

        Args:
            action (AgentDelegateAction): The action containing information about the delegate agent to start.
        """
        agent_cls: type[Agent] = Agent.get_cls(action.agent)
        agent_config = self.agent_configs.get(action.agent, self.agent.config)
        llm_config = self.agent_to_llm_config.get(action.agent, self.agent.llm.config)
        llm = LLM(config=llm_config, retry_listener=self._notify_on_llm_retry)
        delegate_agent = agent_cls(llm=llm, config=agent_config)
        state = State(
            session_id=self.id.removesuffix('-delegate'),
            inputs=action.inputs or {},
            local_iteration=0,
            iteration=self.state.iteration,
            max_iterations=self.state.max_iterations,
            delegate_level=self.state.delegate_level + 1,
            # global metrics should be shared between parent and child
            metrics=self.state.metrics,
            # start on top of the stream
            start_id=self.event_stream.get_latest_event_id() + 1,
        )
        self.log(
            'debug',
            f'start delegate, creating agent {delegate_agent.name} using LLM {llm}',
        )

        # Create the delegate with is_delegate=True so it does NOT subscribe directly
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            agent=delegate_agent,
            event_stream=self.event_stream,
            max_iterations=self.state.max_iterations,
            max_budget_per_task=self.max_budget_per_task,
            agent_to_llm_config=self.agent_to_llm_config,
            agent_configs=self.agent_configs,
            initial_state=state,
            is_delegate=True,
            headless_mode=self.headless_mode,
        )

    def end_delegate(self) -> None:
        """Ends the currently active delegate (e.g., if it is finished or errored).

        so that this controller can resume normal operation.
        """
        if self.delegate is None:
            return

        delegate_state = self.delegate.get_agent_state()

        # update iteration that is shared across agents
        self.state.iteration = self.delegate.state.iteration

        # close the delegate controller before adding new events
        asyncio.get_event_loop().run_until_complete(self.delegate.close())

        if delegate_state in (AgentState.FINISHED, AgentState.REJECTED):
            # retrieve delegate result
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )

            # prepare delegate result observation
            # TODO: replace this with AI-generated summary (#2395)
            formatted_output = ', '.join(
                f'{key}: {value}' for key, value in delegate_outputs.items()
            )
            content = (
                f'{self.delegate.agent.name} finishes task with {formatted_output}'
            )
        else:
            # delegate state is ERROR
            # emit AgentDelegateObservation with error content
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )
            content = (
                f'{self.delegate.agent.name} encountered an error during execution.'
            )

        content = f'Delegated agent finished with result:\n\n{content}'

        # emit the delegate result observation
        obs = AgentDelegateObservation(outputs=delegate_outputs, content=content)

        # associate the delegate action with the initiating tool call
        for event in reversed(self.state.history):
            if isinstance(event, AgentDelegateAction):
                delegate_action = event
                obs.tool_call_metadata = delegate_action.tool_call_metadata
                break

        self.event_stream.add_event(obs, EventSource.AGENT)

        # unset delegate so parent can resume normal handling
        self.delegate = None

    async def _step(self) -> None:
        """Executes a single step of the parent or delegate agent. Detects stuck agents and limits on the number of iterations and the task budget."""
        if self.get_agent_state() != AgentState.RUNNING:
            self.log(
                'info',
                f'Agent not stepping because state is {self.get_agent_state()} (not RUNNING)',
                extra={'msg_type': 'STEP_BLOCKED_STATE'},
            )
            return

        if self._pending_action:
            action_id = getattr(self._pending_action, 'id', 'unknown')
            action_type = type(self._pending_action).__name__
            self.log(
                'info',
                f'Agent not stepping because of pending action: {action_type} (id={action_id})',
                extra={'msg_type': 'STEP_BLOCKED_PENDING_ACTION'},
            )
            return

        self.log(
            'debug',
            f'LEVEL {self.state.delegate_level} LOCAL STEP {self.state.local_iteration} GLOBAL STEP {self.state.iteration}',
            extra={'msg_type': 'STEP'},
        )

        stop_step = False
        if self.state.iteration >= self.state.max_iterations:
            stop_step = await self._handle_traffic_control(
                'iteration', self.state.iteration, self.state.max_iterations
            )
        if self.max_budget_per_task is not None:
            current_cost = self.state.metrics.accumulated_cost
            if current_cost > self.max_budget_per_task:
                stop_step = await self._handle_traffic_control(
                    'budget', current_cost, self.max_budget_per_task
                )
        if stop_step:
            logger.warning('Stopping agent due to traffic control')
            return

        if self._is_stuck():
            await self._react_to_exception(
                AgentStuckInLoopError('Agent got stuck in a loop')
            )
            return

        self.update_state_before_step()
        action: Action = NullAction()

        if self._replay_manager.should_replay():
            # in replay mode, we don't let the agent to proceed
            # instead, we replay the action from the replay trajectory
            action = self._replay_manager.step()
        else:
            try:
                action = self.agent.step(self.state)
                if action is None:
                    raise LLMNoActionError('No action was returned')
                action._source = EventSource.AGENT  # type: ignore [attr-defined]
            except (
                LLMMalformedActionError,
                LLMNoActionError,
                LLMResponseError,
                FunctionCallValidationError,
                FunctionCallNotExistsError,
            ) as e:
                self.event_stream.add_event(
                    ErrorObservation(
                        content=str(e),
                    ),
                    EventSource.AGENT,
                )
                return
            except (ContextWindowExceededError, BadRequestError, OpenAIError) as e:
                # FIXME: this is a hack until a litellm fix is confirmed
                # Check if this is a nested context window error
                # We have to rely on string-matching because LiteLLM doesn't consistently
                # wrap the failure in a ContextWindowExceededError
                error_str = str(e).lower()
                if (
                    'contextwindowexceedederror' in error_str
                    or 'prompt is too long' in error_str
                    or 'input length and `max_tokens` exceed context limit' in error_str
                    or 'please reduce the length of either one'
                    in error_str  # For OpenRouter context window errors
                    or isinstance(e, ContextWindowExceededError)
                ):
                    if self.agent.config.enable_history_truncation:
                        self._handle_long_context_error()
                        return
                    else:
                        raise LLMContextWindowExceedError()
                else:
                    raise e

        if action.runnable:
            if self.state.confirmation_mode and (
                type(action) is CmdRunAction or type(action) is IPythonRunCellAction
            ):
                action.confirmation_state = (
                    ActionConfirmationStatus.AWAITING_CONFIRMATION
                )
            self._pending_action = action

        if not isinstance(action, NullAction):
            if (
                hasattr(action, 'confirmation_state')
                and action.confirmation_state
                == ActionConfirmationStatus.AWAITING_CONFIRMATION
            ):
                await self.set_agent_state_to(AgentState.AWAITING_USER_CONFIRMATION)

            # Create and log metrics for frontend display
            self._prepare_metrics_for_frontend(action)

            self.event_stream.add_event(action, action._source)  # type: ignore [attr-defined]

        await self.update_state_after_step()

        log_level = 'info' if LOG_ALL_EVENTS else 'debug'
        self.log(log_level, str(action), extra={'msg_type': 'ACTION'})

    def _notify_on_llm_retry(self, retries: int, max: int) -> None:
        if self.status_callback is not None:
            msg_id = 'STATUS$LLM_RETRY'
            self.status_callback(
                'info', msg_id, f'Retrying LLM request, {retries} / {max}'
            )

    async def _handle_traffic_control(
        self, limit_type: str, current_value: float, max_value: float
    ) -> bool:
        """Handles agent state after hitting the traffic control limit.

        Args:
            limit_type (str): The type of limit that was hit.
            current_value (float): The current value of the limit.
            max_value (float): The maximum value of the limit.
        """
        stop_step = False
        if self.state.traffic_control_state == TrafficControlState.PAUSED:
            self.log(
                'debug', 'Hitting traffic control, temporarily resume upon user request'
            )
            self.state.traffic_control_state = TrafficControlState.NORMAL
        else:
            self.state.traffic_control_state = TrafficControlState.THROTTLING
            # Format values as integers for iterations, keep decimals for budget
            if limit_type == 'iteration':
                current_str = str(int(current_value))
                max_str = str(int(max_value))
            else:
                current_str = f'{current_value:.2f}'
                max_str = f'{max_value:.2f}'

            if self.headless_mode:
                e = RuntimeError(
                    f'Agent reached maximum {limit_type} in headless mode. '
                    f'Current {limit_type}: {current_str}, max {limit_type}: {max_str}'
                )
                await self._react_to_exception(e)
            else:
                e = RuntimeError(
                    f'Agent reached maximum {limit_type}. '
                    f'Current {limit_type}: {current_str}, max {limit_type}: {max_str}. '
                )
                # FIXME: this isn't really an exception--we should have a different path
                await self._react_to_exception(e)
            stop_step = True
        return stop_step

    @property
    def _pending_action(self) -> Action | None:
        """Get the current pending action with time tracking.

        Returns:
            Action | None: The current pending action, or None if there isn't one.
        """
        if self._pending_action_info is None:
            return None

        action, timestamp = self._pending_action_info
        current_time = time.time()
        elapsed_time = current_time - timestamp

        # Log if the pending action has been active for a long time (but don't clear it)
        if elapsed_time > 60.0:  # 1 minute - just for logging purposes
            action_id = getattr(action, 'id', 'unknown')
            action_type = type(action).__name__
            self.log(
                'warning',
                f'Pending action active for {elapsed_time:.2f}s: {action_type} (id={action_id})',
                extra={'msg_type': 'PENDING_ACTION_TIMEOUT'},
            )

        return action

    @_pending_action.setter
    def _pending_action(self, action: Action | None) -> None:
        """Set or clear the pending action with timestamp and logging.

        Args:
            action: The action to set as pending, or None to clear.
        """
        if action is None:
            if self._pending_action_info is not None:
                prev_action, timestamp = self._pending_action_info
                action_id = getattr(prev_action, 'id', 'unknown')
                action_type = type(prev_action).__name__
                elapsed_time = time.time() - timestamp
                self.log(
                    'debug',
                    f'Cleared pending action after {elapsed_time:.2f}s: {action_type} (id={action_id})',
                    extra={'msg_type': 'PENDING_ACTION_CLEARED'},
                )
            self._pending_action_info = None
        else:
            action_id = getattr(action, 'id', 'unknown')
            action_type = type(action).__name__
            self.log(
                'debug',
                f'Set pending action: {action_type} (id={action_id})',
                extra={'msg_type': 'PENDING_ACTION_SET'},
            )
            self._pending_action_info = (action, time.time())

    def get_state(self) -> State:
        """Returns the current running state object.

        Returns:
            State: The current state object.
        """
        return self.state

    def set_initial_state(
        self,
        state: State | None,
        max_iterations: int,
        confirmation_mode: bool = False,
    ) -> None:
        """Sets the initial state for the agent, either from the previous session, or from a parent agent, or by creating a new one.

        Args:
            state: The state to initialize with, or None to create a new state.
            max_iterations: The maximum number of iterations allowed for the task.
            confirmation_mode: Whether to enable confirmation mode.
        """
        # state can come from:
        # - the previous session, in which case it has history
        # - from a parent agent, in which case it has no history
        # - None / a new state

        # If state is None, we create a brand new state and still load the event stream so we can restore the history
        if state is None:
            self.state = State(
                session_id=self.id.removesuffix('-delegate'),
                inputs={},
                max_iterations=max_iterations,
                confirmation_mode=confirmation_mode,
            )
            self.state.start_id = 0

            self.log(
                'info',
                f'AgentController {self.id} - created new state. start_id: {self.state.start_id}',
            )
        else:
            self.state = state

            if self.state.start_id <= -1:
                self.state.start_id = 0

            self.log(
                'info',
                f'AgentController {self.id} initializing history from event {self.state.start_id}',
            )

        # Always load from the event stream to avoid losing history
        self._init_history()

    def get_trajectory(self, include_screenshots: bool = False) -> list[dict]:
        # state history could be partially hidden/truncated before controller is closed
        assert self._closed
        return [
            event_to_trajectory(event, include_screenshots)
            for event in self.state.history
        ]

    def _init_history(self) -> None:
        """Initializes the agent's history from the event stream.

        The history is a list of events that:
        - Excludes events of types listed in self.filter_out
        - Excludes events with hidden=True attribute
        - For delegate events (between AgentDelegateAction and AgentDelegateObservation):
            - Excludes all events between the action and observation
            - Includes the delegate action and observation themselves
        """
        # define range of events to fetch
        # delegates start with a start_id and initially won't find any events
        # otherwise we're restoring a previous session
        start_id = self.state.start_id if self.state.start_id >= 0 else 0
        end_id = (
            self.state.end_id
            if self.state.end_id >= 0
            else self.event_stream.get_latest_event_id()
        )

        # sanity check
        if start_id > end_id + 1:
            self.log(
                'warning',
                f'start_id {start_id} is greater than end_id + 1 ({end_id + 1}). History will be empty.',
            )
            self.state.history = []
            return

        events: list[Event] = []

        # Get rest of history
        events_to_add = list(
            self.event_stream.get_events(
                start_id=start_id,
                end_id=end_id,
                reverse=False,
                filter_out_type=self.filter_out,
                filter_hidden=True,
            )
        )
        events.extend(events_to_add)

        # Find all delegate action/observation pairs
        delegate_ranges: list[tuple[int, int]] = []
        delegate_action_ids: list[int] = []  # stack of unmatched delegate action IDs

        for event in events:
            if isinstance(event, AgentDelegateAction):
                delegate_action_ids.append(event.id)
                # Note: we can get agent=event.agent and task=event.inputs.get('task','')
                # if we need to track these in the future

            elif isinstance(event, AgentDelegateObservation):
                # Match with most recent unmatched delegate action
                if not delegate_action_ids:
                    self.log(
                        'warning',
                        f'Found AgentDelegateObservation without matching action at id={event.id}',
                    )
                    continue

                action_id = delegate_action_ids.pop()
                delegate_ranges.append((action_id, event.id))

        # Filter out events between delegate action/observation pairs
        if delegate_ranges:
            filtered_events: list[Event] = []
            current_idx = 0

            for start_id, end_id in sorted(delegate_ranges):
                # Add events before delegate range
                filtered_events.extend(
                    event for event in events[current_idx:] if event.id < start_id
                )

                # Add delegate action and observation
                filtered_events.extend(
                    event for event in events if event.id in (start_id, end_id)
                )

                # Update index to after delegate range
                current_idx = next(
                    (i for i, e in enumerate(events) if e.id > end_id), len(events)
                )

            # Add any remaining events after last delegate range
            filtered_events.extend(events[current_idx:])

            self.state.history = filtered_events
        else:
            self.state.history = events

        # make sure history is in sync
        self.state.start_id = start_id

    def _handle_long_context_error(self) -> None:
        # When context window is exceeded, keep roughly half of agent interactions
        kept_events = self._apply_conversation_window()
        kept_event_ids = {e.id for e in kept_events}

        self.log(
            'info',
            f'Context window exceeded. Keeping events with IDs: {kept_event_ids}',
        )

        # The events to forget are those that are not in the kept set
        forgotten_event_ids = {e.id for e in self.state.history} - kept_event_ids

        if len(kept_event_ids) == 0:
            self.log(
                'warning',
                'No events kept after applying conversation window. This should not happen.',
            )

        # verify that the first event id in kept_event_ids is the same as the start_id
        if len(kept_event_ids) > 0 and self.state.history[0].id not in kept_event_ids:
            self.log(
                'warning',
                f'First event after applying conversation window was not kept: {self.state.history[0].id} not in {kept_event_ids}',
            )

        # Add an error event to trigger another step by the agent
        self.event_stream.add_event(
            CondensationAction(
                forgotten_events_start_id=min(forgotten_event_ids)
                if forgotten_event_ids
                else 0,
                forgotten_events_end_id=max(forgotten_event_ids)
                if forgotten_event_ids
                else 0,
            ),
            EventSource.AGENT,
        )

    def _apply_conversation_window(self) -> list[Event]:
        """Cuts history roughly in half when context window is exceeded.

        It preserves action-observation pairs and ensures that the system message,
        the first user message, and its associated recall observation are always included
        at the beginning of the context window.

        The algorithm:
        1. Identify essential initial events: System Message, First User Message, Recall Observation.
        2. Determine the slice of recent events to potentially keep.
        3. Validate the start of the recent slice for dangling observations.
        4. Combine essential events and validated recent events, ensuring essentials come first.

        Args:
            events: List of events to filter

        Returns:
            Filtered list of events keeping newest half while preserving pairs and essential initial events.
        """
        if not self.state.history:
            return []

        history = self.state.history

        # 1. Identify essential initial events
        system_message: SystemMessageAction | None = None
        first_user_msg: MessageAction | None = None
        recall_action: RecallAction | None = None
        recall_observation: Observation | None = None

        # Find System Message (should be the first event, if it exists)
        system_message = next(
            (e for e in history if isinstance(e, SystemMessageAction)), None
        )
        assert (
            system_message is None
            or isinstance(system_message, SystemMessageAction)
            and system_message.id == history[0].id
        )

        # Find First User Message, which MUST exist
        first_user_msg = self._first_user_message()
        if first_user_msg is None:
            raise RuntimeError('No first user message found in the event stream.')

        first_user_msg_index = -1
        for i, event in enumerate(history):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                first_user_msg = event
                first_user_msg_index = i
                break

        # Find Recall Action and Observation related to the First User Message
        if first_user_msg is not None and first_user_msg_index != -1:
            # Look for RecallAction after the first user message
            for i in range(first_user_msg_index + 1, len(history)):
                event = history[i]
                if (
                    isinstance(event, RecallAction)
                    and event.query == first_user_msg.content
                ):
                    # Found RecallAction, now look for its Observation
                    recall_action = event
                    for j in range(i + 1, len(history)):
                        obs_event = history[j]
                        # Check for Observation caused by this RecallAction
                        if (
                            isinstance(obs_event, Observation)
                            and obs_event.cause == recall_action.id
                        ):
                            recall_observation = obs_event
                            break  # Found the observation, stop inner loop
                    break  # Found the recall action (and maybe obs), stop outer loop

        essential_events: list[Event] = []
        if system_message:
            essential_events.append(system_message)
        if first_user_msg:
            essential_events.append(first_user_msg)
        # Also keep the RecallAction that triggered the essential RecallObservation
        if recall_action:
            essential_events.append(recall_action)
        if recall_observation:
            essential_events.append(recall_observation)

        # 2. Determine the slice of recent events to potentially keep
        num_non_essential_events = len(history) - len(essential_events)
        # Keep roughly half of the non-essential events, minimum 1
        num_recent_to_keep = max(1, num_non_essential_events // 2)

        # Calculate the starting index for the recent slice
        slice_start_index = len(history) - num_recent_to_keep
        slice_start_index = max(0, slice_start_index)  # Ensure index is not negative
        recent_events_slice = history[slice_start_index:]

        # 3. Validate the start of the recent slice for dangling observations
        # IMPORTANT: Most observations in history are tool call results, which cannot be without their action, or we get an LLM API error
        first_valid_event_index = 0
        for i, event in enumerate(recent_events_slice):
            if isinstance(event, Observation):
                first_valid_event_index += 1
            else:
                break
        # If all events in the slice are dangling observations, we need to keep at least one
        if first_valid_event_index == len(recent_events_slice):
            self.log(
                'warning',
                'All recent events are dangling observations, which we truncate. This means the agent has only the essential first events. This should not happen.',
            )

        # Adjust the recent_events_slice if dangling observations were found at the start
        if first_valid_event_index < len(recent_events_slice):
            validated_recent_events = recent_events_slice[first_valid_event_index:]
            if first_valid_event_index > 0:
                self.log(
                    'debug',
                    f'Removed {first_valid_event_index} dangling observation(s) from the start of recent event slice.',
                )
        else:
            validated_recent_events = []

        # 4. Combine essential events and validated recent events
        events_to_keep: list[Event] = essential_events + validated_recent_events
        self.log('debug', f'History truncated. Kept {len(events_to_keep)} events.')

        return events_to_keep

    def _is_stuck(self) -> bool:
        """Checks if the agent or its delegate is stuck in a loop.

        Returns:
            bool: True if the agent is stuck, False otherwise.
        """
        # check if delegate stuck
        if self.delegate and self.delegate._is_stuck():
            return True

        return self._stuck_detector.is_stuck(self.headless_mode)

    def _prepare_metrics_for_frontend(self, action: Action) -> None:
        """Create a minimal metrics object for frontend display and log it.

        To avoid performance issues with long conversations, we only keep:
        - accumulated_cost: The current total cost
        - accumulated_token_usage: Accumulated token statistics across all API calls

        This includes metrics from both the agent's LLM and the condenser's LLM if it exists.

        Args:
            action: The action to attach metrics to
        """
        # Get metrics from agent LLM
        agent_metrics = self.agent.llm.metrics

        # Get metrics from condenser LLM if it exists
        condenser_metrics: TokenUsage | None = None
        if hasattr(self.agent, 'condenser') and hasattr(self.agent.condenser, 'llm'):
            condenser_metrics = self.agent.condenser.llm.metrics

        # Create a new minimal metrics object with just what the frontend needs
        metrics = Metrics(model_name=agent_metrics.model_name)

        # Set accumulated cost (sum of agent and condenser costs)
        metrics.accumulated_cost = agent_metrics.accumulated_cost
        if condenser_metrics:
            metrics.accumulated_cost += condenser_metrics.accumulated_cost

        # Set accumulated token usage (sum of agent and condenser token usage)
        # Use a deep copy to ensure we don't modify the original object
        metrics._accumulated_token_usage = (
            agent_metrics.accumulated_token_usage.model_copy(deep=True)
        )
        if condenser_metrics:
            metrics._accumulated_token_usage = (
                metrics._accumulated_token_usage
                + condenser_metrics.accumulated_token_usage
            )

        action.llm_metrics = metrics

        # Log the metrics information for debugging
        # Get the latest usage directly from the agent's metrics
        latest_usage = None
        if self.agent.llm.metrics.token_usages:
            latest_usage = self.agent.llm.metrics.token_usages[-1]

        accumulated_usage = self.agent.llm.metrics.accumulated_token_usage
        self.log(
            'debug',
            f'Action metrics - accumulated_cost: {metrics.accumulated_cost}, '
            f'latest tokens (prompt/completion/cache_read/cache_write): '
            f'{latest_usage.prompt_tokens if latest_usage else 0}/'
            f'{latest_usage.completion_tokens if latest_usage else 0}/'
            f'{latest_usage.cache_read_tokens if latest_usage else 0}/'
            f'{latest_usage.cache_write_tokens if latest_usage else 0}, '
            f'accumulated tokens (prompt/completion): '
            f'{accumulated_usage.prompt_tokens}/'
            f'{accumulated_usage.completion_tokens}',
            extra={'msg_type': 'METRICS'},
        )

    def __repr__(self) -> str:
        pending_action_info = '<none>'
        if (
            hasattr(self, '_pending_action_info')
            and self._pending_action_info is not None
        ):
            action, timestamp = self._pending_action_info
            action_id = getattr(action, 'id', 'unknown')
            action_type = type(action).__name__
            elapsed_time = time.time() - timestamp
            pending_action_info = (
                f'{action_type}(id={action_id}, elapsed={elapsed_time:.2f}s)'
            )

        return (
            f'AgentController(id={getattr(self, "id", "<uninitialized>")}, '
            f'agent={getattr(self, "agent", "<uninitialized>")!r}, '
            f'event_stream={getattr(self, "event_stream", "<uninitialized>")!r}, '
            f'state={getattr(self, "state", "<uninitialized>")!r}, '
            f'delegate={getattr(self, "delegate", "<uninitialized>")!r}, '
            f'_pending_action={pending_action_info})'
        )

    def _is_awaiting_observation(self) -> bool:
        events = self.event_stream.get_events(reverse=True)
        for event in events:
            if isinstance(event, AgentStateChangedObservation):
                result = event.agent_state == AgentState.RUNNING
                return result
        return False

    def _first_user_message(self) -> MessageAction | None:
        """Get the first user message for this agent.

        For regular agents, this is the first user message from the beginning (start_id=0).
        For delegate agents, this is the first user message after the delegate's start_id.

        Returns:
            MessageAction | None: The first user message, or None if no user message found
        """
        # Return cached message if any
        if self._cached_first_user_message is not None:
            return self._cached_first_user_message

        # Find the first user message
        self._cached_first_user_message = next(
            (
                e
                for e in self.event_stream.get_events(
                    start_id=self.state.start_id,
                )
                if isinstance(e, MessageAction) and e.source == EventSource.USER
            ),
            None,
        )
        return self._cached_first_user_message
