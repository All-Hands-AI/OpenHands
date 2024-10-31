import asyncio
import time

from fastapi import WebSocket, WebSocketDisconnect

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.const.guide_url import TROUBLESHOOTING_URL
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema import AgentState
from openhands.core.schema.action import ActionType
from openhands.core.schema.config import ConfigType
from openhands.events.action import ChangeAgentStateAction, MessageAction, NullAction
from openhands.events.event import Event, EventSource
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    NullObservation,
)
from openhands.events.observation.error import ErrorObservation
from openhands.events.serialization import event_from_dict, event_to_dict
from openhands.events.stream import EventStreamSubscriber
from openhands.llm.llm import LLM
from openhands.runtime.utils.shutdown_listener import should_continue
from openhands.server.session.agent_session import AgentSession
from openhands.storage.files import FileStore


class Session:
    sid: str
    websocket: WebSocket | None
    last_active_ts: int = 0
    is_alive: bool = True
    agent_session: AgentSession
    loop: asyncio.AbstractEventLoop

    def __init__(
        self, sid: str, ws: WebSocket | None, config: AppConfig, file_store: FileStore
    ):
        self.sid = sid
        self.websocket = ws
        self.last_active_ts = int(time.time())
        self.agent_session = AgentSession(sid, file_store)
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event
        )
        self.config = config
        self.loop = asyncio.get_event_loop()

    async def close(self):
        self.is_alive = False
        await self.agent_session.close()

    async def loop_recv(self):
        try:
            if self.websocket is None:
                return
            while should_continue():
                try:
                    data = await self.websocket.receive_json()
                except ValueError:
                    await self.send_error('Invalid JSON')
                    continue
                await self.dispatch(data)
        except WebSocketDisconnect:
            await self.close()
            logger.debug('WebSocket disconnected, sid: %s', self.sid)
        except RuntimeError as e:
            await self.close()
            logger.exception('Error in loop_recv: %s', e)

    def _set_loading_state(self):
        """Set the initial loading state for the agent."""
        self.agent_session.event_stream.add_event(
            ChangeAgentStateAction(AgentState.LOADING), EventSource.ENVIRONMENT
        )
        self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )

    def _extract_config_args(self, data: dict) -> tuple[dict, str, int]:
        """Extract and process configuration arguments from the request data."""
        args = {key: value for key, value in data.get('args', {}).items()}
        agent_cls = args.get(ConfigType.AGENT, self.config.default_agent)
        
        # Update security settings
        self.config.security.confirmation_mode = args.get(
            ConfigType.CONFIRMATION_MODE, self.config.security.confirmation_mode
        )
        self.config.security.security_analyzer = data.get('args', {}).get(
            ConfigType.SECURITY_ANALYZER, self.config.security.security_analyzer
        )
        
        max_iterations = args.get(ConfigType.MAX_ITERATIONS, self.config.max_iterations)
        return args, agent_cls, max_iterations

    def _configure_llm(self, args: dict, default_llm_config):
        """Configure LLM settings from provided arguments."""
        default_llm_config.model = args.get(
            ConfigType.LLM_MODEL, default_llm_config.model
        )
        default_llm_config.api_key = args.get(
            ConfigType.LLM_API_KEY, default_llm_config.api_key
        )
        default_llm_config.base_url = args.get(
            ConfigType.LLM_BASE_URL, default_llm_config.base_url
        )
        # TODO: override other LLM config & agent config groups (#2075)

    async def _start_agent_session(self, agent, max_iterations: int):
        """Start the agent session with the configured parameters."""
        try:
            await self.agent_session.start(
                runtime_name=self.config.runtime,
                config=self.config,
                agent=agent,
                max_iterations=max_iterations,
                max_budget_per_task=self.config.max_budget_per_task,
                agent_to_llm_config=self.config.get_agent_to_llm_config_map(),
                agent_configs=self.config.get_agent_configs(),
                status_message_callback=self.queue_status_message,
            )
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information..'
            )
            raise

    async def _initialize_agent(self, data: dict):
        """Initialize the agent with the provided configuration."""
        self._set_loading_state()
        
        # Extract configuration
        args, agent_cls, max_iterations = self._extract_config_args(data)
        
        # Configure LLM
        default_llm_config = self.config.get_llm_config()
        self._configure_llm(args, default_llm_config)
        
        # Create agent
        llm = LLM(config=self.config.get_llm_config_from_agent(agent_cls))
        agent_config = self.config.get_agent_config(agent_cls)
        agent = Agent.get_cls(agent_cls)(llm, agent_config)
        
        # Start agent session
        try:
            await self._start_agent_session(agent, max_iterations)
        except Exception:
            return

    def _should_skip_event(self, event: Event) -> bool:
        """Check if the event should be skipped."""
        return isinstance(event, (NullAction, NullObservation))

    def _is_environment_feedback_event(self, event: Event) -> bool:
        """Check if the event is environment feedback that should be treated as agent event."""
        return (
            event.source == EventSource.ENVIRONMENT 
            and isinstance(event, (CmdOutputObservation, AgentStateChangedObservation))
        )

    async def _send_as_agent_event(self, event: Event):
        """Send an event to the UI marked as coming from the agent."""
        event_dict = event_to_dict(event)
        event_dict['source'] = EventSource.AGENT
        await self.send(event_dict)

    async def on_event(self, event: Event):
        """Callback function for events that mainly come from the agent.
        Event is the base class for any agent action and observation.

        Args:
            event: The agent event (Observation or Action).
        """
        if self._should_skip_event(event):
            return

        if event.source == EventSource.AGENT:
            await self.send(event_to_dict(event))
        # NOTE: ipython observations are not sent here currently
        elif self._is_environment_feedback_event(event):
            # feedback from the environment to agent actions is understood as agent events by the UI
            await self._send_as_agent_event(event)
        elif isinstance(event, ErrorObservation):
            # send error events as agent events to the UI
            await self._send_as_agent_event(event)

    async def dispatch(self, data: dict):
        action = data.get('action', '')
        if action == ActionType.INIT:
            await self._initialize_agent(data)
            return
        event = event_from_dict(data.copy())
        # This checks if the model supports images
        if isinstance(event, MessageAction) and event.images_urls:
            controller = self.agent_session.controller
            if controller:
                if controller.agent.llm.config.disable_vision:
                    await self.send_error(
                        'Support for images is disabled for this model, try without an image.'
                    )
                    return
                if not controller.agent.llm.vision_is_active():
                    await self.send_error(
                        'Model does not support image upload, change to a different model or try without an image.'
                    )
                    return
        if self.agent_session.loop:
            asyncio.run_coroutine_threadsafe(
                self._add_event(event, EventSource.USER), self.agent_session.loop
            )  # type: ignore

    async def _add_event(self, event, event_source):
        self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> bool:
        try:
            if self.websocket is None or not self.is_alive:
                return False
            await self.websocket.send_json(data)
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except RuntimeError:
            self.is_alive = False
            return False
        except WebSocketDisconnect:
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send({'error': True, 'message': message})

    async def send_status_message(self, message: str) -> bool:
        """Sends a status message to the client."""
        return await self.send({'status': message})

    def queue_status_message(self, message: str):
        """Queues a status message to be sent asynchronously."""
        # Ensure the coroutine runs in the main event loop
        asyncio.run_coroutine_threadsafe(self.send_status_message(message), self.loop)
