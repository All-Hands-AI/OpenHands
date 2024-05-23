import asyncio
import time

from fastapi import WebSocket, WebSocketDisconnect

from opendevin.core.const.guide_url import TROUBLESHOOTING_URL
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import AgentState
from opendevin.core.schema.action import ActionType
from opendevin.events.action import ChangeAgentStateAction, NullAction
from opendevin.events.event import Event, EventSource
from opendevin.events.observation import AgentStateChangedObservation, NullObservation
from opendevin.events.serialization import event_from_dict, event_to_dict
from opendevin.events.stream import EventStreamSubscriber

from .agent import AgentSession

DEL_DELT_SEC = 60 * 60 * 5


class Session:
    sid: str
    websocket: WebSocket | None
    last_active_ts: int = 0
    is_alive: bool = True
    agent_session: AgentSession

    def __init__(self, sid: str, ws: WebSocket | None):
        self.sid = sid
        self.websocket = ws
        self.last_active_ts = int(time.time())
        self.agent_session = AgentSession(sid)
        self.agent_session.event_stream.subscribe(
            EventStreamSubscriber.SERVER, self.on_event
        )

    async def close(self):
        self.is_alive = False
        await self.agent_session.close()

    async def loop_recv(self):
        try:
            if self.websocket is None:
                return
            while True:
                try:
                    data = await self.websocket.receive_json()
                except ValueError:
                    await self.send_error('Invalid JSON')
                    continue
                await self.dispatch(data)
        except WebSocketDisconnect:
            await self.close()
            logger.info('WebSocket disconnected, sid: %s', self.sid)
        except RuntimeError as e:
            await self.close()
            logger.exception('Error in loop_recv: %s', e)

    async def _initialize_agent(self, data: dict):
        await self.agent_session.event_stream.add_event(
            ChangeAgentStateAction(AgentState.LOADING), EventSource.USER
        )
        await self.agent_session.event_stream.add_event(
            AgentStateChangedObservation('', AgentState.LOADING), EventSource.AGENT
        )
        try:
            await self.agent_session.start(data)
        except Exception as e:
            logger.exception(f'Error creating controller: {e}')
            await self.send_error(
                f'Error creating controller. Please check Docker is running and visit `{TROUBLESHOOTING_URL}` for more debugging information..'
            )
            return
        await self.agent_session.event_stream.add_event(
            ChangeAgentStateAction(AgentState.INIT), EventSource.USER
        )

    async def on_event(self, event: Event):
        """Callback function for agent events.

        Args:
            event: The agent event (Observation or Action).
        """
        if isinstance(event, NullAction):
            return
        if isinstance(event, NullObservation):
            return
        if event.source == EventSource.AGENT and not isinstance(
            event, (NullAction, NullObservation)
        ):
            await self.send(event_to_dict(event))

    async def dispatch(self, data: dict):
        action = data.get('action', '')
        if action == ActionType.INIT:
            await self._initialize_agent(data)
            return
        event = event_from_dict(data.copy())
        await self.agent_session.event_stream.add_event(event, EventSource.USER)

    async def send(self, data: dict[str, object]) -> bool:
        try:
            if self.websocket is None or not self.is_alive:
                return False
            await self.websocket.send_json(data)
            await asyncio.sleep(0.001)  # This flushes the data to the client
            self.last_active_ts = int(time.time())
            return True
        except WebSocketDisconnect:
            self.is_alive = False
            return False

    async def send_error(self, message: str) -> bool:
        """Sends an error message to the client."""
        return await self.send({'error': True, 'message': message})

    async def send_message(self, message: str) -> bool:
        """Sends a message to the client."""
        return await self.send({'message': message})

    def update_connection(self, ws: WebSocket):
        self.websocket = ws
        self.is_alive = True
        self.last_active_ts = int(time.time())

    def load_from_data(self, data: dict) -> bool:
        self.last_active_ts = data.get('last_active_ts', 0)
        if self.last_active_ts < int(time.time()) - DEL_DELT_SEC:
            return False
        self.is_alive = data.get('is_alive', False)
        return True
