import asyncio
import copy
import os
import traceback
from typing import Callable, ClassVar, Type

import litellm
from litellm.exceptions import (
    BadRequestError,
    ContextWindowExceededError,
    RateLimitError,
)

from openhands.controller.agent import Agent
from openhands.controller.state.state import State, TrafficControlState
from openhands.controller.stuck import StuckDetector
from openhands.core.config import AgentConfig, LLMConfig
from openhands.core.exceptions import (
    AgentStuckInLoopError,
    FunctionCallNotExistsError,
    FunctionCallValidationError,
    LLMMalformedActionError,
    LLMNoActionError,
    LLMResponseError,
)
from openhands.core.logger import LOG_ALL_EVENTS
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream, EventStreamSubscriber
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
)
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

# note: RESUME is only available on web GUI
TRAFFIC_CONTROL_REMINDER = (
    "Please click on resume button if you'd like to continue, or start a new task."
)


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
    _pending_action: Action | None = None
    _closed: bool = False
    filter_out: ClassVar[tuple[type[Event], ...]] = (
        NullAction,
        NullObservation,
        ChangeAgentStateAction,
        AgentStateChangedObservation,
    )

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        max_iterations: int,
        max_budget_per_task: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        sid: str = 'default',
        confirmation_mode: bool = False,
        initial_state: State | None = None,
        is_delegate: bool = False,
        headless_mode: bool = True,
        status_callback: Callable | None = None,
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
        """
        self.id = sid
        self.agent = agent
        self.headless_mode = headless_mode

        # subscribe to the event stream
        self.event_stream = event_stream
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

    async def close(self) -> None:
        """Closes the agent controller, canceling any ongoing tasks and unsubscribing from the event stream.

        Note that it's fairly important that this closes properly, otherwise the state is incomplete.
        """
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
        self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER, self.id)
        self._closed = True

    def log(self, level: str, message: str, extra: dict | None = None) -> None:
        """Logs a message to the agent controller's logger.

        Args:
            level (str): The logging level to use (e.g., 'info', 'debug', 'error').
            message (str): The message to log.
            extra (dict | None, optional): Additional fields to include in the log. Defaults to None.
        """
        message = f'[Agent Controller {self.id}] {message}'
        getattr(logger, level)(message, extra=extra, stacklevel=2)

    def update_state_before_step(self):
        self.state.iteration += 1
        self.state.local_iteration += 1

    async def update_state_after_step(self):
        # update metrics especially for cost. Use deepcopy to avoid it being modified by agent._reset()
        self.state.local_metrics = copy.deepcopy(self.agent.llm.metrics)

    async def _react_to_exception(
        self,
        e: Exception,
    ):
        """React to an exception by setting the agent state to error and sending a status message."""
        await self.set_agent_state_to(AgentState.ERROR)
        if self.status_callback is not None:
            err_id = ''
            if isinstance(e, litellm.AuthenticationError):
                err_id = 'STATUS$ERROR_LLM_AUTHENTICATION'
            elif isinstance(e, RateLimitError):
                await self.set_agent_state_to(AgentState.RATE_LIMITED)
                return
            self.status_callback('error', err_id, type(e).__name__ + ': ' + str(e))

    def step(self):
        asyncio.create_task(self._step_with_exception_handling())

    async def _step_with_exception_handling(self):
        try:
            await self._step()
        except Exception as e:
            self.log(
                'error',
                f'Error while running the agent (session ID: {self.id}): {e}. '
                f'Traceback: {traceback.format_exc()}',
            )
            reported = RuntimeError(
                'There was an unexpected error while running the agent. Please '
                f'report this error to the developers. Your session ID is {self.id}. '
                f'Error type: {e.__class__.__name__}'
            )
            if isinstance(e, litellm.AuthenticationError) or isinstance(
                e, litellm.BadRequestError
            ):
                reported = e
            await self._react_to_exception(reported)

    def should_step(self, event: Event) -> bool:
        if isinstance(event, Action):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return True
            return False
        if isinstance(event, Observation):
            if isinstance(event, NullObservation) or isinstance(
                event, AgentStateChangedObservation
            ):
                return False
            return True
        return False

    def on_event(self, event: Event) -> None:
        """Callback from the event stream. Notifies the controller of incoming events.

        Args:
            event (Event): The incoming event to process.
        """
        asyncio.get_event_loop().run_until_complete(self._on_event(event))

    async def _on_event(self, event: Event) -> None:
        if hasattr(event, 'hidden') and event.hidden:
            return

        # if the event is not filtered out, add it to the history
        if not any(isinstance(event, filter_type) for filter_type in self.filter_out):
            self.state.history.append(event)

        if isinstance(event, Action):
            await self._handle_action(event)
        elif isinstance(event, Observation):
            await self._handle_observation(event)

        if self.should_step(event):
            self.step()

    async def _handle_action(self, action: Action) -> None:
        """Handles actions from the event stream.

        Args:
            action (Action): The action to handle.
        """
        if isinstance(action, ChangeAgentStateAction):
            await self.set_agent_state_to(action.agent_state)  # type: ignore
        elif isinstance(action, MessageAction):
            await self._handle_message_action(action)
        elif isinstance(action, AgentDelegateAction):
            await self.start_delegate(action)

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
            if self.get_agent_state() != AgentState.RUNNING:
                await self.set_agent_state_to(AgentState.RUNNING)
        elif action.source == EventSource.AGENT and action.wait_for_response:
            await self.set_agent_state_to(AgentState.AWAITING_USER_INPUT)

    def _reset(self) -> None:
        """Resets the agent controller"""
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
                obs = ErrorObservation(content='The action has not been executed.')
                obs.tool_call_metadata = self._pending_action.tool_call_metadata
                obs._cause = self._pending_action.id  # type: ignore[attr-defined]
                self.event_stream.add_event(obs, EventSource.AGENT)

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
        self.event_stream.add_event(
            AgentStateChangedObservation('', self.state.agent_state),
            EventSource.ENVIRONMENT,
        )

        if new_state == AgentState.INIT and self.state.resume_state:
            await self.set_agent_state_to(self.state.resume_state)
            self.state.resume_state = None

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
        agent_cls: Type[Agent] = Agent.get_cls(action.agent)
        agent_config = self.agent_configs.get(action.agent, self.agent.config)
        llm_config = self.agent_to_llm_config.get(action.agent, self.agent.llm.config)
        llm = LLM(config=llm_config)
        delegate_agent = agent_cls(llm=llm, config=agent_config)
        state = State(
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

        self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER, self.id)
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
        await self.delegate.set_agent_state_to(AgentState.RUNNING)

    async def _step(self) -> None:
        """Executes a single step of the parent or delegate agent. Detects stuck agents and limits on the number of iterations and the task budget."""
        if self.get_agent_state() != AgentState.RUNNING:
            return

        if self._pending_action:
            return

        if self.delegate is not None:
            assert self.delegate != self
            # TODO this conditional will always be false, because the parent controllers are unsubscribed
            # remove if it's still useless when delegation is reworked
            if self.delegate.get_agent_state() != AgentState.PAUSED:
                await self._delegate_step()
            return

        self.log(
            'info',
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
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise LLMNoActionError('No action was returned')
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
        except (ContextWindowExceededError, BadRequestError) as e:
            # FIXME: this is a hack until a litellm fix is confirmed
            # Check if this is a nested context window error
            error_str = str(e).lower()
            if (
                'contextwindowexceedederror' in error_str
                or 'prompt is too long' in error_str
                or isinstance(e, ContextWindowExceededError)
            ):
                # When context window is exceeded, keep roughly half of agent interactions
                self.state.history = self._apply_conversation_window(self.state.history)

                # Save the ID of the first event in our truncated history for future reloading
                if self.state.history:
                    self.state.start_id = self.state.history[0].id
                # Don't add error event - let the agent retry with reduced context
                return
            raise

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
            self.event_stream.add_event(action, EventSource.AGENT)

        await self.update_state_after_step()

        log_level = 'info' if LOG_ALL_EVENTS else 'debug'
        self.log(log_level, str(action), extra={'msg_type': 'ACTION'})

    async def _delegate_step(self) -> None:
        """Executes a single step of the delegate agent."""
        await self.delegate._step()  # type: ignore[union-attr]
        assert self.delegate is not None
        delegate_state = self.delegate.get_agent_state()
        self.log('debug', f'Delegate state: {delegate_state}')
        if delegate_state == AgentState.ERROR:
            # update iteration that shall be shared across agents
            self.state.iteration = self.delegate.state.iteration

            # emit AgentDelegateObservation to mark delegate termination due to error
            delegate_outputs = (
                self.delegate.state.outputs if self.delegate.state else {}
            )
            content = (
                f'{self.delegate.agent.name} encountered an error during execution.'
            )
            obs = AgentDelegateObservation(outputs=delegate_outputs, content=content)
            self.event_stream.add_event(obs, EventSource.AGENT)

            # close the delegate upon error
            await self.delegate.close()

            # resubscribe parent when delegate is finished
            self.event_stream.subscribe(
                EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, self.id
            )
            self.delegate = None
            self.delegateAction = None

        elif delegate_state in (AgentState.FINISHED, AgentState.REJECTED):
            self.log('debug', 'Delegate agent has finished execution')
            # retrieve delegate result
            outputs = self.delegate.state.outputs if self.delegate.state else {}

            # update iteration that shall be shared across agents
            self.state.iteration = self.delegate.state.iteration

            # close delegate controller: we must close the delegate controller before adding new events
            await self.delegate.close()

            # resubscribe parent when delegate is finished
            self.event_stream.subscribe(
                EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, self.id
            )

            # update delegate result observation
            # TODO: replace this with AI-generated summary (#2395)
            formatted_output = ', '.join(
                f'{key}: {value}' for key, value in outputs.items()
            )
            content = (
                f'{self.delegate.agent.name} finishes task with {formatted_output}'
            )
            obs = AgentDelegateObservation(outputs=outputs, content=content)

            # clean up delegate status
            self.delegate = None
            self.delegateAction = None
            self.event_stream.add_event(obs, EventSource.AGENT)
        return

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
                inputs={},
                max_iterations=max_iterations,
                confirmation_mode=confirmation_mode,
            )
            self.state.start_id = 0

            self.log(
                'debug',
                f'AgentController {self.id} - created new state. start_id: {self.state.start_id}',
            )
        else:
            self.state = state

            if self.state.start_id <= -1:
                self.state.start_id = 0

            self.log(
                'debug',
                f'AgentController {self.id} initializing history from event {self.state.start_id}',
            )

        # Always load from the event stream to avoid losing history
        self._init_history()

    def _init_history(self) -> None:
        """Initializes the agent's history from the event stream.

        The history is a list of events that:
        - Excludes events of types listed in self.filter_out
        - Excludes events with hidden=True attribute
        - For delegate events (between AgentDelegateAction and AgentDelegateObservation):
            - Excludes all events between the action and observation
            - Includes the delegate action and observation themselves

        The history is loaded in two parts if truncation_id is set:
        1. First user message from start_id onwards
        2. Rest of history from truncation_id to the end

        Otherwise loads normally from start_id.
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

        # If we have a truncation point, get first user message and then rest of history
        if hasattr(self.state, 'truncation_id') and self.state.truncation_id > 0:
            # Find first user message from stream
            first_user_msg = next(
                (
                    e
                    for e in self.event_stream.get_events(
                        start_id=start_id,
                        end_id=end_id,
                        reverse=False,
                        filter_out_type=self.filter_out,
                        filter_hidden=True,
                    )
                    if isinstance(e, MessageAction) and e.source == EventSource.USER
                ),
                None,
            )
            if first_user_msg:
                events.append(first_user_msg)

            # the rest of the events are from the truncation point
            start_id = self.state.truncation_id

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

    def _apply_conversation_window(self, events: list[Event]) -> list[Event]:
        """Cuts history roughly in half when context window is exceeded, preserving action-observation pairs
        and ensuring the first user message is always included.

        The algorithm:
        1. Cut history in half
        2. Check first event in new history:
           - If Observation: find and include its Action
           - If MessageAction: ensure its related Action-Observation pair isn't split
        3. Always include the first user message

        Args:
            events: List of events to filter

        Returns:
            Filtered list of events keeping newest half while preserving pairs
        """
        if not events:
            return events

        # Find first user message - we'll need to ensure it's included
        first_user_msg = next(
            (
                e
                for e in events
                if isinstance(e, MessageAction) and e.source == EventSource.USER
            ),
            None,
        )

        # cut in half
        mid_point = max(1, len(events) // 2)
        kept_events = events[mid_point:]

        # Handle first event in truncated history
        if kept_events:
            i = 0
            while i < len(kept_events):
                first_event = kept_events[i]
                if isinstance(first_event, Observation) and first_event.cause:
                    # Find its action and include it
                    matching_action = next(
                        (
                            e
                            for e in reversed(events[:mid_point])
                            if isinstance(e, Action) and e.id == first_event.cause
                        ),
                        None,
                    )
                    if matching_action:
                        kept_events = [matching_action] + kept_events
                    else:
                        self.log(
                            'warning',
                            f'Found Observation without matching Action at id={first_event.id}',
                        )
                        # drop this observation
                        kept_events = kept_events[1:]
                    break

                elif isinstance(first_event, MessageAction) or (
                    isinstance(first_event, Action)
                    and first_event.source == EventSource.USER
                ):
                    # if it's a message action or a user action, keep it and continue to find the next event
                    i += 1
                    continue

                else:
                    # if it's an action with source == EventSource.AGENT, we're good
                    break

        # Save where to continue from in next reload
        if kept_events:
            self.state.truncation_id = kept_events[0].id

        # Ensure first user message is included
        if first_user_msg and first_user_msg not in kept_events:
            kept_events = [first_user_msg] + kept_events

        # start_id points to first user message
        if first_user_msg:
            self.state.start_id = first_user_msg.id

        return kept_events

    def _is_stuck(self) -> bool:
        """Checks if the agent or its delegate is stuck in a loop.

        Returns:
            bool: True if the agent is stuck, False otherwise.
        """
        # check if delegate stuck
        if self.delegate and self.delegate._is_stuck():
            return True

        return self._stuck_detector.is_stuck(self.headless_mode)

    def __repr__(self):
        return (
            f'AgentController(id={getattr(self, "id", "<uninitialized>")}, '
            f'agent={getattr(self, "agent", "<uninitialized>")!r}, '
            f'event_stream={getattr(self, "event_stream", "<uninitialized>")!r}, '
            f'state={getattr(self, "state", "<uninitialized>")!r}, '
            f'delegate={getattr(self, "delegate", "<uninitialized>")!r}, '
            f'_pending_action={getattr(self, "_pending_action", "<uninitialized>")!r})'
        )

    def _is_awaiting_observation(self):
        events = self.event_stream.get_events(reverse=True)
        for event in events:
            if isinstance(event, AgentStateChangedObservation):
                result = event.agent_state == AgentState.RUNNING
                return result
        return False
