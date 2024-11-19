import asyncio
import time
from dataclasses import dataclass, field

import socketio

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.agent import AgentState
from openhands.events.event import EventSource
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.serialization.event import event_to_dict
from openhands.events.stream import session_exists
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import Session
from openhands.storage.files import FileStore
from openhands.utils.shutdown_listener import should_continue


@dataclass
class SessionManager:
    config: AppConfig
    file_store: FileStore
    local_sessions_by_sid: dict[str, Session] = field(default_factory=dict)
    local_sessions_by_connection_id: dict[str, Session] = field(default_factory=dict)

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        start_time = time.time()
        if not await session_exists(sid, self.file_store):
            return None
        c = Conversation(sid, file_store=self.file_store, config=self.config)
        await c.connect()
        end_time = time.time()
        logger.info(
            f'Conversation {c.sid} connected in {end_time - start_time} seconds'
        )
        return c

    async def detach_from_conversation(self, conversation: Conversation):
        await conversation.disconnect()

    async def init_or_join_local_session(self, sio: socketio.AsyncServer, sid: str, connection_id: str, data: dict):
        """ If there is no local session running, initialize one """
        session = self.local_sessions_by_sid.get(sid)
        if not session:
            # I think we need to rehydrate here, but it does not seem to be working
            session = Session(
                sid=sid, file_store=self.file_store, config=self.config, sio=sio
            )
            session.connect(connection_id)
            self.local_sessions_by_sid[sid] = session
            self.local_sessions_by_connection_id[connection_id] = session
            await session.initialize_agent(data)
        else:
            session.connect(connection_id)
            self.local_sessions_by_connection_id[connection_id] = session
            session.agent_session.event_stream.add_event(AgentStateChangedObservation('', AgentState.INIT), EventSource.ENVIRONMENT)
        return session
    
    def get_local_session(self, connection_id: str) -> Session:
        return self.local_sessions_by_connection_id[connection_id]
    
    async def disconnect_from_local_session(self, connection_id: str):
        session = self.local_sessions_by_connection_id.pop(connection_id, None)
        if not session:
            # This can occur if the init action was never run.
            logger.warning(f'disconnect_from_uninitialized_session:{connection_id}')
            return
        if session.disconnect(connection_id):
            if should_continue():
                asyncio.create_task(self._check_and_close_session(session))
            else:
                await self._check_and_close_session(session)
            
    async def _check_and_close_session(self, session: Session):
        # Once there have been no connections to a session for a reasonable period, we close it
        try:
            await asyncio.sleep(self.config.sandbox.close_delay)
        finally:
            # If the sleep was cancelled, we still want to close these
            if not session.connection_ids:
                session.close()
                self.local_sessions_by_sid.pop(session.sid, None)