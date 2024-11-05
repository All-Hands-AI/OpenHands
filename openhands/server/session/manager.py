import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from fastapi import WebSocket

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.stream import session_exists
from openhands.runtime.utils.shutdown_listener import should_continue
from openhands.server.session.conversation import Conversation
from openhands.server.session.session import Session
from openhands.storage.files import FileStore


@dataclass
class SessionManager:
    config: AppConfig
    file_store: FileStore
    cleanup_interval: int = 300
    session_timeout: int = 600
    _sessions: dict[str, Session] = field(default_factory=dict)
    _session_cleanup_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        if not self._session_cleanup_task:
            self._session_cleanup_task = asyncio.create_task(self._cleanup_sessions())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._session_cleanup_task:
            self._session_cleanup_task.cancel()
            self._session_cleanup_task = None

    def add_or_restart_session(self, sid: str, ws_conn: WebSocket) -> Session:
        """Add a new session or restart an existing one.
        
        Args:
            sid: Session ID
            ws_conn: WebSocket connection
            
        Returns:
            Session: The new or restarted session
            
        Raises:
            ValueError: If sid is empty or invalid
            RuntimeError: If session creation fails
        """
        if not sid or not isinstance(sid, str):
            raise ValueError('Invalid session ID')
            
        if not ws_conn:
            raise ValueError('WebSocket connection is required')
            
        try:
            # Close existing session if any
            if sid in self._sessions:
                try:
                    self._sessions[sid].close()
                except Exception as e:
                    logger.warning(f'Error closing existing session {sid}: {str(e)}')
                    
            # Create new session
            session = Session(
                sid=sid,
                file_store=self.file_store,
                ws=ws_conn,
                config=self.config
            )
            self._sessions[sid] = session
            logger.debug(f'Created new session: {sid}')
            return session
            
        except Exception as e:
            logger.error(f'Failed to create session {sid}: {str(e)}', exc_info=True)
            raise RuntimeError(f'Session creation failed: {str(e)}')

    def get_session(self, sid: str) -> Session | None:
        if sid not in self._sessions:
            return None
        return self._sessions.get(sid)

    async def attach_to_conversation(self, sid: str) -> Conversation | None:
        """Attach to an existing conversation.
        
        Args:
            sid: Session ID to attach to
            
        Returns:
            Conversation | None: The conversation if successful, None if session doesn't exist
            
        Raises:
            ValueError: If sid is empty or invalid
            RuntimeError: If conversation creation or connection fails
        """
        if not sid or not isinstance(sid, str):
            raise ValueError('Invalid session ID')
            
        try:
            # Check if session exists
            if not await session_exists(sid, self.file_store):
                logger.debug(f'No existing session found for {sid}')
                return None
                
            # Create conversation
            try:
                conversation = Conversation(
                    sid=sid,
                    file_store=self.file_store,
                    config=self.config
                )
            except Exception as e:
                logger.error(f'Failed to create conversation for {sid}: {str(e)}')
                raise RuntimeError(f'Conversation creation failed: {str(e)}')
                
            # Connect conversation
            try:
                await conversation.connect()
            except Exception as e:
                logger.error(f'Failed to connect conversation for {sid}: {str(e)}')
                raise RuntimeError(f'Conversation connection failed: {str(e)}')
                
            logger.debug(f'Successfully attached to conversation: {sid}')
            return conversation
            
        except Exception as e:
            logger.error(f'Unexpected error attaching to conversation {sid}: {str(e)}', exc_info=True)
            raise

    async def detach_from_conversation(self, conversation: Conversation | None):
        """Detach from a conversation, cleaning up resources.
        
        Args:
            conversation: The conversation to detach from, or None
            
        Raises:
            RuntimeError: If disconnection fails
        """
        if not conversation:
            return
            
        try:
            await conversation.disconnect()
        except Exception as e:
            logger.error(f'Error disconnecting conversation: {str(e)}')
            raise RuntimeError(f'Failed to disconnect conversation: {str(e)}')

    async def send(self, sid: str, data: dict[str, object]) -> bool:
        """Send data to a client session.
        
        Args:
            sid: Session ID to send to
            data: Data to send
            
        Returns:
            bool: True if send was successful, False otherwise
            
        Raises:
            ValueError: If sid is empty/invalid or data is not a dict
        """
        if not sid or not isinstance(sid, str):
            raise ValueError('Invalid session ID')
            
        if not isinstance(data, dict):
            raise ValueError('Data must be a dictionary')
            
        try:
            session = self.get_session(sid)
            if session is None:
                logger.error(f'No session found for {sid}, skipping message')
                return False
                
            if not session.is_alive:
                logger.warning(f'Session {sid} is no longer alive, skipping message')
                return False
                
            return await session.send(data)
            
        except Exception as e:
            logger.error(f'Error sending data to session {sid}: {str(e)}')
            return False

    async def send_error(self, sid: str, message: str) -> bool:
        """Send an error message to a client session.
        
        Args:
            sid: Session ID to send to
            message: Error message to send
            
        Returns:
            bool: True if send was successful, False otherwise
            
        Raises:
            ValueError: If sid is empty/invalid or message is not a string
        """
        if not message or not isinstance(message, str):
            raise ValueError('Invalid error message')
            
        return await self.send(sid, {
            'error': True,
            'message': message
        })

    async def send_message(self, sid: str, message: str) -> bool:
        """Send a regular message to a client session.
        
        Args:
            sid: Session ID to send to
            message: Message to send
            
        Returns:
            bool: True if send was successful, False otherwise
            
        Raises:
            ValueError: If sid is empty/invalid or message is not a string
        """
        if not message or not isinstance(message, str):
            raise ValueError('Invalid message')
            
        return await self.send(sid, {'message': message})

    async def _cleanup_sessions(self):
        while should_continue():
            current_time = time.time()
            session_ids_to_remove = []
            for sid, session in list(self._sessions.items()):
                # if session inactive for a long time, remove it
                if (
                    not session.is_alive
                    and current_time - session.last_active_ts > self.session_timeout
                ):
                    session_ids_to_remove.append(sid)

            for sid in session_ids_to_remove:
                try:
                    to_del_session: Session | None = self._sessions.pop(sid, None)
                    if to_del_session is not None:
                        to_del_session.close()
                        logger.debug(
                            f'Session {sid} and related resource have been removed due to inactivity.'
                        )
                except (RuntimeError, asyncio.CancelledError) as e:
                    # Handle errors during session cleanup gracefully
                    logger.warning(f'Error while cleaning up session {sid}: {str(e)}')

            await asyncio.sleep(self.cleanup_interval)
