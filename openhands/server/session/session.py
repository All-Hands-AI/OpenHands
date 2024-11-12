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
        self.agent_session = AgentSession(
            sid, file_store, status_callback=self.queue_status_message
        )
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event, self.sid
        )
        self.config = config
        self.loop = asyncio.get_event_loop()

    def close(self):
        self.is_alive = False
        self.agent_session.close()

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
            logger.info('WebSocket disconnected, sid: %s', self.sid)
            self.close()
        except RuntimeError as e:
            logger.exception('Error in loop_recv: %s', e)
            self.close()

    async def _initialize_agent(self, data: dict):
        self.agent_session.event_stream.add_event(
            ChangeAgentStateAction(AgentState.LOADING), EventSource.ENVIRONMENT
        )
        self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING),
            EventSource.ENVIRONMENT,
        )
        # Extract the agent-relevant arguments from the request
        args = {key: value for key, value in data.get('args', {}).items()}
        agent_cls = args.get(ConfigType.AGENT, self.config.default_agent)
        self.config.security.confirmation_mode = args.get(
            ConfigType.CONFIRMATION_MODE, self.config.security.confirmation_mode
        )
        self.config.security.security_analyzer = data.get('args', {}).get(
            ConfigType.SECURITY_ANALYZER, self.config.security.security_analyzer
        )
        max_iterations = args.get(ConfigType.MAX_ITERATIONS, self.config.max_iterations)
        # override default LLM config
        default_llm_config = self.config.get_llm_config()
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

        llm = LLM(config=self.config.get_llm_config_from_agent(agent_cls))
        agent_config = self.config.get_agent_config(agent_cls)
        agent = Agent.get_cls(agent_cls)(llm, agent_config)

        # Create the agent session
        try:
            await self.agent_session.start(
                runtime_name=self.config.runtime,
                config=self.config,
                agent=agent,
                max_iterations=max_iterations,
                max_budget_per_task=self.config.max_budget_per_task,
                agent_to_llm_config=self.config.get_agent_to_llm_config_map(),
                agent_configs=self.config.get_agent_configs(),
            )
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information..'
            )
            return

    async def on_event(self, event: Event):
        """Callback function for events that mainly come from the agent.
        Event is the base class for any agent action and observation.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == EventSource.AGENT:
            await self.send(event_to_dict(event))
        elif event.source == EventSource.USER and isinstance(
            event, CmdOutputObservation
        ):
            await self.send(event_to_dict(event))
        # NOTE: ipython observations are not sent here currently
        elif event.source == EventSource.ENVIRONMENT and isinstance(
            event, (CmdOutputObservation, AgentStateChangedObservation)
        ):
            # feedback from the environment to agent actions is understood as agent events by the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)
        elif isinstance(event, ErrorObservation):
            # send error events as agent events to the UI
            event_dict = event_to_dict(event)
            event_dict['source'] = EventSource.AGENT
            await self.send(event_dict)

    async def dispatch(self, data: dict):
        action = data.get('action', '')
        if action == ActionType.INIT:
            await self._initialize_agent(data)
            return
        event = event_from_dict(data.copy())
        # This checks if the model supports images
        if isinstance(event, MessageAction) and event.image_urls:
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
        self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> bool:
        try:
            if self.websocket is None or not self.is_alive:
                return False
            await self.websocket.send_json(data)
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except (RuntimeError, WebSocketDisconnect):
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send({'error': True, 'message': message})

    async def _send_status_message(self, msg_type: str, id: str, message: str) -> bool:
        """Sends a status message to the client."""
        if msg_type == 'error':
            await self.agent_session.stop_agent_loop_for_error()

        return await self.send(
            {'status_update': True, 'type': msg_type, 'id': id, 'message': message}
        )

    def queue_status_message(self, msg_type: str, id: str, message: str):
        """Queues a status message to be sent asynchronously."""
        asyncio.run_coroutine_threadsafe(
            self._send_status_message(msg_type, id, message), self.loop
        )
