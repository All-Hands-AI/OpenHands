from __future__ import annotations

import asyncio
import copy
import os
import time
import traceback
from typing import Callable

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
from openhands.controller.state.state import State
from openhands.controller.state.state_tracker import StateTracker
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
from openhands.events.serialization.event import truncate_content
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics, TokenUsage
from openhands.memory.view import View
from openhands.storage.files import FileStore

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
    _cached_first_user_message: MessageAction | None = None

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        iteration_delta: int,
        budget_per_task_delta: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        sid: str | None = None,
        file_store: FileStore | None = None,
        user_id: str | None = None,
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
        self.user_id = user_id
        self.file_store = file_store
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

        self.state_tracker = StateTracker(sid, file_store, user_id)

        # state from the previous session, state from a parent agent, or a fresh state
        self.set_initial_state(
            state=initial_state,
            max_iterations=iteration_delta,
            max_budget_per_task=budget_per_task_delta,
            confirmation_mode=confirmation_mode,
        )

        self.state = self.state_tracker.state  # TODO: share between manager and controller for backward compatability; we should ideally move all state related logic to the state manager

        self.agent_to_llm_config = agent_to_llm_config if agent_to_llm_config else {}
        self.agent_configs = agent_configs if agent_configs else {}
        self._initial_max_iterations = iteration_delta
        self._initial_max_budget_per_task = budget_per_task_delta

        # stuck helper
        self._stuck_detector = StuckDetector(self.state)
        self.status_callback = status_callback

        # replay-related
        self._replay_manager = ReplayManager(replay_events)

        # Add the system message to the event stream
        self._add_system_message()

    def _add_system_message(self):
        for event in self.event_stream.search_events(start_id=self.state.start_id):
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
        if system_message and system_message.content:
            preview = (
                system_message.content[:50] + '...'
                if len(system_message.content) > 50
                else system_message.content
            )
            logger.debug(f'System message: {preview}')
            self.event_stream.add_event(system_message, EventSource.AGENT)

    async def close(self, set_stop_state: bool = True) -> None:
        """Closes the agent controller, canceling any ongoing tasks and unsubscribing from the event stream.

        Note that it's fairly important that this closes properly, otherwise the state is incomplete.
        """
        if set_stop_state:
            await self.set_agent_state_to(AgentState.STOPPED)

        self.state_tracker.close(self.event_stream)

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
            if (
                delegate_state
                not in (
                    AgentState.FINISHED,
                    AgentState.ERROR,
                    AgentState.REJECTED,
                )
                or 'RuntimeError: Agent reached maximum iteration.'
                in self.delegate.state.last_error
                or 'RuntimeError:Agent reached maximum budget for conversation'
                in self.delegate.state.last_error
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

        self.state_tracker.add_history(event)

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
            await self.set_agent_state_to(AgentState.FINISHED)
        elif isinstance(action, AgentRejectAction):
            self.state.outputs = action.outputs
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

        # TODO: these metrics come from the draft editor, and they get accumulated into controller's state metrics and the agent's llm metrics
        # In the future, we should have a more principled way to sharing metrics across all LLM instances for a given conversation
        if observation.llm_metrics is not None:
            self.state_tracker.merge_metrics(observation.llm_metrics)

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
            self._reset()

        # User is allowing to check control limits and expand them if applicable
        if (
            self.state.agent_state == AgentState.ERROR
            and new_state == AgentState.RUNNING
        ):
            self.state_tracker.maybe_increase_control_flags_limits(self.headless_mode)

        if self._pending_action is not None and (
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

        # Save state whenever agent state changes to ensure we don't lose state
        # in case of crashes or unexpected circumstances
        self.save_state()

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
        # Make sure metrics are shared between parent and child for global accumulation
        llm = LLM(
            config=llm_config,
            retry_listener=self.agent.llm.retry_listener,
            metrics=self.state.metrics,
        )
        delegate_agent = agent_cls(llm=llm, config=agent_config)

        # Take a snapshot of the current metrics before starting the delegate
        state = State(
            session_id=self.id.removesuffix('-delegate'),
            inputs=action.inputs or {},
            iteration_flag=self.state.iteration_flag,
            budget_flag=self.state.budget_flag,
            delegate_level=self.state.delegate_level + 1,
            # global metrics should be shared between parent and child
            metrics=self.state.metrics,
            # start on top of the stream
            start_id=self.event_stream.get_latest_event_id() + 1,
            parent_metrics_snapshot=self.state_tracker.get_metrics_snapshot(),
            parent_iteration=self.state.iteration_flag.current_value,
        )
        self.log(
            'debug',
            f'start delegate, creating agent {delegate_agent.name} using LLM {llm}',
        )

        # Create the delegate with is_delegate=True so it does NOT subscribe directly
        self.delegate = AgentController(
            sid=self.id + '-delegate',
            file_store=self.file_store,
            user_id=self.user_id,
            agent=delegate_agent,
            event_stream=self.event_stream,
            iteration_delta=self._initial_max_iterations,
            budget_per_task_delta=self._initial_max_budget_per_task,
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
        self.state.iteration_flag.current_value = (
            self.delegate.state.iteration_flag.current_value
        )

        # Calculate delegate-specific metrics before closing the delegate
        delegate_metrics = self.state.get_local_metrics()
        logger.info(f'Local metrics for delegate: {delegate_metrics}')

        # close the delegate controller before adding new events
        asyncio.get_event_loop().run_until_complete(self.delegate.close())

        if delegate_state in (AgentState.FINISHED, AgentState.REJECTED):
            # retrieve delegate result
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )

            # prepare delegate result observation
            # TODO: replace this with AI-generated summary (#2395)
            # Filter out metrics from the formatted output to avoid clutter
            display_outputs = {
                k: v for k, v in delegate_outputs.items() if k != 'metrics'
            }
            formatted_output = ', '.join(
                f'{key}: {value}' for key, value in display_outputs.items()
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
                'debug',
                f'Agent not stepping because state is {self.get_agent_state()} (not RUNNING)',
                extra={'msg_type': 'STEP_BLOCKED_STATE'},
            )
            return

        if self._pending_action:
            action_id = getattr(self._pending_action, 'id', 'unknown')
            action_type = type(self._pending_action).__name__
            self.log(
                'debug',
                f'Agent not stepping because of pending action: {action_type} (id={action_id})',
                extra={'msg_type': 'STEP_BLOCKED_PENDING_ACTION'},
            )
            return

        self.log(
            'debug',
            f'LEVEL {self.state.delegate_level} LOCAL STEP {self.state.get_local_step()} GLOBAL STEP {self.state.iteration_flag.current_value}',
            extra={'msg_type': 'STEP'},
        )

        # Ensure budget control flag is synchronized with the latest metrics.
        # In the future, we should centralized the use of one LLM object per conversation.
        # This will help us unify the cost for auto generating titles, running the condensor, etc.
        # Before many microservices will touh the same llm cost field, we should sync with the budget flag for the controller
        # and check that we haven't exceeded budget BEFORE executing an agent step.
        self.state_tracker.sync_budget_flag_with_metrics()

        if self._is_stuck():
            await self._react_to_exception(
                AgentStuckInLoopError('Agent got stuck in a loop')
            )
            return

        try:
            self.state_tracker.run_control_flags()
        except Exception as e:
            logger.warning('Control flag limits hit')
            await self._react_to_exception(e)
            return

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

        log_level = 'info' if LOG_ALL_EVENTS else 'debug'
        self.log(log_level, str(action), extra={'msg_type': 'ACTION'})

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
        max_budget_per_task: float | None,
        confirmation_mode: bool = False,
    ):
        self.state_tracker.set_initial_state(
            self.id,
            self.agent,
            state,
            max_iterations,
            max_budget_per_task,
            confirmation_mode,
        )
        # Always load from the event stream to avoid losing history
        self.state_tracker._init_history(
            self.event_stream,
        )

    def get_trajectory(self, include_screenshots: bool = False) -> list[dict]:
        # state history could be partially hidden/truncated before controller is closed
        assert self._closed
        return self.state_tracker.get_trajectory(include_screenshots)

    def _handle_long_context_error(self) -> None:
        # When context window is exceeded, keep roughly half of agent interactions
        current_view = View.from_events(self.state.history)
        kept_events = self._apply_conversation_window(current_view.events)
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

    def _apply_conversation_window(self, history: list[Event]) -> list[Event]:
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
        # Handle empty history
        if not history:
            return []
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

        # Find First User Message in the history, which MUST exist
        first_user_msg = self._first_user_message(history)
        if first_user_msg is None:
            # If not found in history, try the event stream
            first_user_msg = self._first_user_message()
            if first_user_msg is None:
                raise RuntimeError('No first user message found in the event stream.')
            self.log(
                'warning',
                'First user message not found in history. Using cached version from event stream.',
            )

        # Find the first user message index in the history
        first_user_msg_index = -1
        for i, event in enumerate(history):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                first_user_msg_index = i
                break

        # Find Recall Action and Observation related to the First User Message
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
        # Only include first user message if history is not empty
        if history:
            essential_events.append(first_user_msg)
            # Include recall action and observation if both exist
            if recall_action and recall_observation:
                essential_events.append(recall_action)
                essential_events.append(recall_observation)
            # Include recall action without observation for backward compatibility
            elif recall_action:
                essential_events.append(recall_action)

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
        agent_metrics = self.state.metrics

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
        if self.state.metrics.token_usages:
            latest_usage = self.state.metrics.token_usages[-1]

        accumulated_usage = self.state.metrics.accumulated_token_usage
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
        events = self.event_stream.search_events(reverse=True)
        for event in events:
            if isinstance(event, AgentStateChangedObservation):
                result = event.agent_state == AgentState.RUNNING
                return result
        return False

    def _first_user_message(
        self, events: list[Event] | None = None
    ) -> MessageAction | None:
        """Get the first user message for this agent.

        For regular agents, this is the first user message from the beginning (start_id=0).
        For delegate agents, this is the first user message after the delegate's start_id.

        Args:
            events: Optional list of events to search through. If None, uses the event stream.

        Returns:
            MessageAction | None: The first user message, or None if no user message found
        """
        # If events list is provided, search through it
        if events is not None:
            return next(
                (
                    e
                    for e in events
                    if isinstance(e, MessageAction) and e.source == EventSource.USER
                ),
                None,
            )

        # Otherwise, use the original event stream logic with caching
        # Return cached message if any
        if self._cached_first_user_message is not None:
            return self._cached_first_user_message

        # Find the first user message
        self._cached_first_user_message = next(
            (
                e
                for e in self.event_stream.search_events(
                    start_id=self.state.start_id,
                )
                if isinstance(e, MessageAction) and e.source == EventSource.USER
            ),
            None,
        )
        return self._cached_first_user_message

    def save_state(self):
        self.state_tracker.save_state()
