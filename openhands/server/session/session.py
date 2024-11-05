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
        """Initialize a new session.
        
        Args:
            sid: Session ID
            ws: WebSocket connection (optional)
            config: Application configuration
            file_store: File storage instance
            
        Raises:
            ValueError: If required parameters are invalid
            RuntimeError: If initialization fails
        """
        # Validate inputs
        if not sid or not isinstance(sid, str):
            raise ValueError('Invalid session ID')
        if not config:
            raise ValueError('Configuration is required')
        if not file_store:
            raise ValueError('File store is required')
            
        try:
            self.sid = sid
            self.websocket = ws
            self.last_active_ts = int(time.time())
            self.config = config
            
            # Initialize agent session
            try:
                self.agent_session = AgentSession(sid, file_store)
                self.agent_session.event_stream.subscribe(
                    EventStreamSubscriber.SERVER, self.on_event
                )
                logger.debug(f'Initialized agent session for {sid}')
            except Exception as e:
                logger.error(f'Failed to initialize agent session: {str(e)}')
                raise RuntimeError(f'Agent session initialization failed: {str(e)}')
                
            # Get event loop
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError as e:
                logger.error('No event loop in current thread')
                raise RuntimeError(f'Event loop initialization failed: {str(e)}')
                
        except Exception as e:
            logger.error(f'Failed to initialize session: {str(e)}', exc_info=True)
            raise

    def close(self):
        """Close the session and clean up resources.
        
        This method ensures proper cleanup of all session resources including:
        - Agent session
        - WebSocket connection
        - Event subscriptions
        
        The method attempts to clean up as much as possible even if errors occur,
        logging any issues for debugging.
        """
        logger.debug(f'Closing session {self.sid}')
        
        # Mark session as closed
        self.is_alive = False
        
        # Clean up agent session
        if hasattr(self, 'agent_session'):
            try:
                self.agent_session.close()
                logger.debug(f'Closed agent session for {self.sid}')
            except Exception as e:
                logger.error(f'Error closing agent session: {str(e)}')
        
        # Clean up websocket
        if self.websocket:
            try:
                asyncio.create_task(self.websocket.close())
                logger.debug(f'Closed websocket for {self.sid}')
            except Exception as e:
                logger.error(f'Error closing websocket: {str(e)}')
            self.websocket = None
            
        # Clear event loop reference
        if hasattr(self, 'loop'):
            self.loop = None
            
        logger.info(f'Session {self.sid} closed')

    async def loop_recv(self):
        """Main receive loop for WebSocket messages.
        
        This method continuously receives and processes messages from the WebSocket
        connection until the connection is closed or an error occurs.
        
        The loop handles:
        - JSON parsing errors
        - WebSocket disconnections
        - Runtime errors
        - Message dispatch
        
        Notes:
            - The loop exits if the WebSocket is not available
            - Invalid JSON messages are reported but don't stop the loop
            - Any unhandled error leads to session closure
        """
        if self.websocket is None:
            logger.warning(f'No WebSocket connection for session {self.sid}')
            return
            
        try:
            logger.debug(f'Starting receive loop for session {self.sid}')
            
            while should_continue() and self.is_alive:
                try:
                    # Receive and parse message
                    try:
                        data = await self.websocket.receive_json()
                    except ValueError as e:
                        logger.warning(f'Invalid JSON received: {str(e)}')
                        await self.send_error('Invalid JSON format in message')
                        continue
                    except WebSocketDisconnect:
                        logger.info(f'WebSocket disconnected for session {self.sid}')
                        raise
                        
                    # Validate message format
                    if not isinstance(data, dict):
                        logger.warning('Received non-dictionary message')
                        await self.send_error('Message must be a JSON object')
                        continue
                        
                    # Dispatch message
                    try:
                        await self.dispatch(data)
                    except Exception as e:
                        logger.error(f'Error dispatching message: {str(e)}')
                        await self.send_error(f'Failed to process message: {str(e)}')
                        continue
                        
                except WebSocketDisconnect:
                    logger.info(f'WebSocket disconnected for session {self.sid}')
                    break
                except RuntimeError as e:
                    logger.error(f'Runtime error in receive loop: {str(e)}')
                    break
                except Exception as e:
                    logger.error(f'Unexpected error in receive loop: {str(e)}', exc_info=True)
                    await self.send_error('Internal server error')
                    break
                    
        finally:
            # Ensure cleanup happens
            logger.debug(f'Exiting receive loop for session {self.sid}')
            self.close()

    async def _initialize_agent(self, data: dict):
        """Initialize the agent with the provided configuration.
        
        This method sets up the agent with the specified configuration and starts
        the agent session. It handles configuration validation, LLM setup, and
        agent initialization.
        
        Args:
            data: Configuration data for agent initialization
            
        Raises:
            ValueError: If configuration data is invalid
            RuntimeError: If agent initialization fails
        """
        if not isinstance(data, dict):
            raise ValueError('Configuration data must be a dictionary')
            
        try:
            # Update agent state
            self.agent_session.event_stream.add_event(
                ChangeAgentStateAction(AgentState.LOADING), EventSource.ENVIRONMENT
            )
            self.agent_session.event_stream.add_event(
                AgentStateChangedObservation('', AgentState.LOADING),
                EventSource.ENVIRONMENT,
            )
            
            # Extract and validate arguments
            args = data.get('args', {})
            if not isinstance(args, dict):
                raise ValueError('Arguments must be a dictionary')
                
            # Get agent class
            agent_cls = args.get(ConfigType.AGENT, self.config.default_agent)
            if not agent_cls:
                raise ValueError('Agent class not specified')
                
            # Update security configuration
            self.config.security.confirmation_mode = args.get(
                ConfigType.CONFIRMATION_MODE, self.config.security.confirmation_mode
            )
            self.config.security.security_analyzer = args.get(
                ConfigType.SECURITY_ANALYZER, self.config.security.security_analyzer
            )
            
            # Get and validate iterations
            max_iterations = args.get(ConfigType.MAX_ITERATIONS, self.config.max_iterations)
            if not isinstance(max_iterations, int) or max_iterations < 1:
                raise ValueError('Invalid max iterations value')
                
            # Configure LLM
            try:
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
                
                llm_config = self.config.get_llm_config_from_agent(agent_cls)
                llm = LLM(config=llm_config)
                logger.debug(f'Configured LLM with model: {llm_config.model}')
            except Exception as e:
                logger.error(f'Failed to configure LLM: {str(e)}')
                raise RuntimeError(f'LLM configuration failed: {str(e)}')
                
            # Initialize agent
            try:
                agent_config = self.config.get_agent_config(agent_cls)
                agent = Agent.get_cls(agent_cls)(llm, agent_config)
                logger.debug(f'Initialized agent: {agent_cls}')
            except Exception as e:
                logger.error(f'Failed to initialize agent: {str(e)}')
                raise RuntimeError(f'Agent initialization failed: {str(e)}')
                
            # Start agent session
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
                logger.debug('Successfully started agent session')
            except Exception as e:
                logger.error(f'Failed to start agent session: {str(e)}', exc_info=True)
                await self.send_error(
                    f'Error starting agent. Please check Docker is running and visit {TROUBLESHOOTING_URL} '
                    f'for debugging information. Error: {str(e)}'
                )
                raise RuntimeError(f'Agent session start failed: {str(e)}')
                
        except Exception as e:
            logger.error(f'Agent initialization failed: {str(e)}', exc_info=True)
            await self.send_error(str(e))
            raise

    async def on_event(self, event: Event):
        """Handle events from the agent and environment.
        
        This callback function processes events from various sources and routes them
        appropriately. It handles agent actions, environment feedback, and error
        observations.
        
        Args:
            event: The event to process (Action or Observation)
            
        Raises:
            ValueError: If event is invalid
            RuntimeError: If event processing fails
            
        Notes:
            - NullAction and NullObservation events are ignored
            - Environment events are converted to agent events for UI
            - Error events are always sent to the UI
            - IPython observations are currently not handled
        """
        if not isinstance(event, Event):
            raise ValueError('Invalid event type')
            
        try:
            # Skip null events
            if isinstance(event, (NullAction, NullObservation)):
                return
                
            # Convert event to dictionary format
            try:
                event_dict = event_to_dict(event)
            except Exception as e:
                logger.error(f'Failed to convert event to dictionary: {str(e)}')
                raise RuntimeError(f'Event serialization failed: {str(e)}')
                
            # Handle different event types
            if event.source == EventSource.AGENT:
                # Direct agent events
                await self.send(event_dict)
                
            elif event.source == EventSource.ENVIRONMENT and isinstance(
                event, (CmdOutputObservation, AgentStateChangedObservation)
            ):
                # Environment feedback converted to agent events
                event_dict['source'] = EventSource.AGENT
                await self.send(event_dict)
                
            elif isinstance(event, ErrorObservation):
                # Error events always sent as agent events
                event_dict['source'] = EventSource.AGENT
                await self.send(event_dict)
                
            else:
                # Log unhandled event types for debugging
                logger.debug(
                    f'Unhandled event type: {type(event).__name__} '
                    f'from source: {event.source}'
                )
                
        except Exception as e:
            logger.error(f'Event handling failed: {str(e)}', exc_info=True)
            # Try to send error to UI if possible
            try:
                await self.send_error(f'Failed to process event: {str(e)}')
            except Exception:
                pass  # Ignore errors in error handling
            raise

    async def dispatch(self, data: dict):
        """Dispatch an event based on the received data.
        
        This method handles different types of events and routes them appropriately.
        It performs validation and ensures the event can be handled by the current
        configuration.
        
        Args:
            data: Event data to dispatch
            
        Raises:
            ValueError: If event data is invalid
            RuntimeError: If dispatch fails
        """
        if not isinstance(data, dict):
            raise ValueError('Event data must be a dictionary')
            
        try:
            # Get and validate action
            action = data.get('action', '')
            if not action:
                raise ValueError('No action specified in event data')
                
            # Handle initialization
            if action == ActionType.INIT:
                await self._initialize_agent(data)
                return
                
            # Convert data to event
            try:
                event = event_from_dict(data.copy())
            except Exception as e:
                logger.error(f'Failed to parse event data: {str(e)}')
                raise ValueError(f'Invalid event format: {str(e)}')
                
            # Handle image support
            if isinstance(event, MessageAction) and event.images_urls:
                controller = self.agent_session.controller
                if not controller:
                    raise RuntimeError('Agent controller not initialized')
                    
                # Check vision support
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
                    
            # Add event to loop
            if not self.loop:
                raise RuntimeError('No event loop available')
                
            try:
                asyncio.run_coroutine_threadsafe(
                    self._add_event(event, EventSource.USER),
                    self.loop
                )
            except Exception as e:
                logger.error(f'Failed to add event to loop: {str(e)}')
                raise RuntimeError(f'Event dispatch failed: {str(e)}')
                
        except Exception as e:
            logger.error(f'Event dispatch failed: {str(e)}', exc_info=True)
            await self.send_error(str(e))
            raise

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
        except (RuntimeError, WebSocketDisconnect):
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
