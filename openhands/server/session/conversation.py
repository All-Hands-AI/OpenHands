import asyncio

from openhands.core.config import AppConfig
from openhands.events.stream import EventStream
from openhands.runtime import get_runtime_cls
from openhands.runtime.base import Runtime
from openhands.security import SecurityAnalyzer, options
from openhands.storage.files import FileStore
from openhands.utils.async_utils import call_sync_from_async


class Conversation:
    sid: str
    file_store: FileStore
    event_stream: EventStream
    runtime: Runtime

    def __init__(
        self,
        sid: str,
        file_store: FileStore,
        config: AppConfig,
    ):
        """Initialize a new conversation.
        
        Args:
            sid: Session ID
            file_store: File storage instance
            config: Application configuration
            
        Raises:
            ValueError: If any required parameter is invalid
            RuntimeError: If initialization fails
        """
        # Validate inputs
        if not sid or not isinstance(sid, str):
            raise ValueError('Invalid session ID')
        if not file_store:
            raise ValueError('File store is required')
        if not config:
            raise ValueError('Configuration is required')
            
        try:
            self.sid = sid
            self.config = config
            self.file_store = file_store
            
            # Initialize event stream
            try:
                self.event_stream = EventStream(sid, file_store)
            except Exception as e:
                logger.error(f'Failed to create event stream: {str(e)}')
                raise RuntimeError(f'Event stream initialization failed: {str(e)}')
            
            # Initialize security analyzer if configured
            self.security_analyzer = None
            if config.security.security_analyzer:
                try:
                    analyzer_cls = options.SecurityAnalyzers.get(
                        config.security.security_analyzer, SecurityAnalyzer
                    )
                    self.security_analyzer = analyzer_cls(self.event_stream)
                    logger.debug(f'Initialized security analyzer: {config.security.security_analyzer}')
                except Exception as e:
                    logger.error(f'Failed to initialize security analyzer: {str(e)}')
                    raise RuntimeError(f'Security analyzer initialization failed: {str(e)}')
            
            # Initialize runtime
            try:
                runtime_cls = get_runtime_cls(self.config.runtime)
                self.runtime = runtime_cls(
                    config=config,
                    event_stream=self.event_stream,
                    sid=self.sid,
                    attach_to_existing=True,
                )
                logger.debug(f'Initialized runtime for session {sid}')
            except Exception as e:
                logger.error(f'Failed to initialize runtime: {str(e)}')
                raise RuntimeError(f'Runtime initialization failed: {str(e)}')
                
        except Exception as e:
            logger.error(f'Failed to initialize conversation: {str(e)}', exc_info=True)
            raise

    async def connect(self):
        """Connect the conversation's runtime.
        
        This method establishes the connection for the runtime component
        of the conversation.
        
        Raises:
            RuntimeError: If runtime is not initialized
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        if not self.runtime:
            raise RuntimeError('Runtime not initialized')
            
        try:
            logger.debug(f'Connecting runtime for session {self.sid}')
            await self.runtime.connect()
            logger.debug(f'Successfully connected runtime for session {self.sid}')
            
        except ConnectionError as e:
            logger.error(f'Connection failed for session {self.sid}: {str(e)}')
            raise
            
        except asyncio.TimeoutError as e:
            logger.error(f'Connection timed out for session {self.sid}: {str(e)}')
            raise TimeoutError(f'Runtime connection timed out: {str(e)}')
            
        except Exception as e:
            logger.error(f'Unexpected error connecting runtime for session {self.sid}: {str(e)}', exc_info=True)
            raise RuntimeError(f'Runtime connection failed: {str(e)}')

    async def disconnect(self):
        """Disconnect the conversation's runtime.
        
        This method gracefully closes the runtime connection and cleans up
        resources. It attempts to handle errors gracefully to ensure resources
        are properly released.
        """
        if not self.runtime:
            logger.debug(f'No runtime to disconnect for session {self.sid}')
            return
            
        try:
            logger.debug(f'Disconnecting runtime for session {self.sid}')
            # Create task for async cleanup
            cleanup_task = asyncio.create_task(
                call_sync_from_async(self.runtime.close)
            )
            
            # Wait for cleanup with timeout
            try:
                await asyncio.wait_for(cleanup_task, timeout=10.0)
                logger.debug(f'Successfully disconnected runtime for session {self.sid}')
            except asyncio.TimeoutError:
                logger.warning(f'Runtime disconnect timed out for session {self.sid}')
                cleanup_task.cancel()
                
        except RuntimeError as e:
            logger.warning(f'Error during runtime disconnect for session {self.sid}: {str(e)}')
        except asyncio.CancelledError:
            logger.warning(f'Runtime disconnect was cancelled for session {self.sid}')
        except Exception as e:
            logger.error(f'Unexpected error during runtime disconnect for session {self.sid}: {str(e)}')
            
        # Cleanup security analyzer if present
        if self.security_analyzer:
            try:
                await self.security_analyzer.close()
            except Exception as e:
                logger.warning(f'Error closing security analyzer for session {self.sid}: {str(e)}')
